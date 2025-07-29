import os
import sys
import uuid
import pandas as pd
import numpy as np
from flask import (
    Blueprint, render_template, request, redirect, url_for, session,
    send_from_directory, flash, jsonify, current_app
)
from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler
from werkzeug.utils import secure_filename

# Import helper functions from our processing module
from .processing import get_df_info, read_file

# Create a Blueprint
main_bp = Blueprint('main', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_file_path(folder_key, filename):
    return os.path.join(current_app.config[folder_key], filename)


@main_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'warning'); return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'warning'); return redirect(request.url)
            
        if file and allowed_file(file.filename):
            session_id = str(uuid.uuid4())
            safe_filename = secure_filename(file.filename)
            upload_path = get_file_path('UPLOAD_FOLDER', f"{session_id}_{safe_filename}")
            file.save(upload_path)
            
            df = read_file(upload_path)
            if df is None:
                flash("Could not read the uploaded file.", "danger"); return redirect(request.url)

            base_filename = f"{session_id}_base.csv"
            df.to_csv(get_file_path('CLEANED_FOLDER', base_filename), index=False)
            
            session.clear()
            session['session_id'] = session_id
            
            session['checkpoints'] = [{
                'name': 'Base (Initial Load)',
                'filename': base_filename,
                'full_code': f"# Initial Load from '{safe_filename}'\ndf = pd.read_csv('{safe_filename}')",
            }]
            return redirect(url_for('main.workspace'))
        else:
            flash('Invalid file type.', 'danger'); return redirect(request.url)
            
    return render_template('index.html')

@main_bp.route('/workspace', methods=['GET', 'POST'])
def workspace():
    if 'checkpoints' not in session or not session['checkpoints']:
        flash("No active session. Please upload a file to begin.", "warning")
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        base_checkpoint_file = request.form.get('base_checkpoint')
        start_df_path = get_file_path('CLEANED_FOLDER', base_checkpoint_file)
        start_df = pd.read_csv(start_df_path, low_memory=False)

        df_cleaned = start_df.copy()
        code_snippets = [f"\n# --- Operations based on Checkpoint: '{base_checkpoint_file}' ---"]

        # --- FULL BLOCK OF CLEANING OPERATIONS ---

        # 1. Drop Columns
        cols_to_drop = request.form.getlist('drop_columns')
        if cols_to_drop:
            df_cleaned.drop(columns=cols_to_drop, inplace=True, errors='ignore')
            code_snippets.append(f"\ndf.drop(columns={cols_to_drop}, inplace=True, errors='ignore')")
        
        # 2. Handle Missing Values
        na_cols, na_action = request.form.getlist('na_columns'), request.form.get('na_action')
        if na_cols and na_action:
            code_snippets.append("\n# Handle missing values")
            if na_action == 'drop_rows':
                df_cleaned.dropna(subset=na_cols, inplace=True)
                code_snippets.append(f"df.dropna(subset={na_cols}, inplace=True)")
            else:
                for col in na_cols:
                    if col in df_cleaned.columns:
                        try:
                            if na_action == 'fill_mean': value, code_val = df_cleaned[col].mean(), f"df['{col}'].mean()"
                            elif na_action == 'fill_median': value, code_val = df_cleaned[col].median(), f"df['{col}'].median()"
                            elif na_action == 'fill_mode': value, code_val = df_cleaned[col].mode()[0], f"df['{col}'].mode()[0]"
                            elif na_action == 'fill_custom':
                                custom_val = request.form.get('na_custom_value')
                                try: value, code_val = float(custom_val), custom_val
                                except ValueError: value, code_val = custom_val, f"'{custom_val}'"
                            df_cleaned[col] = df_cleaned[col].fillna(value)
                            code_snippets.append(f"df['{col}'] = df['{col}'].fillna({code_val})")
                        except Exception as e: code_snippets.append(f"# WARNING: Could not fill NA for '{col}': {e}")
        
        type_cols = request.form.getlist('type_columns')
        new_type = request.form.get('new_type')
        rounding_method = request.form.get('rounding_method') # Get the rounding method

        if type_cols and new_type:
            code_snippets.append(f"\n# Convert columns to type: {new_type}")
            for col in type_cols:
                if col in df_cleaned.columns:
                    try:
                        current_dtype = df_cleaned[col].dtype

                        # SCENARIO 1: Converting TO a nullable integer (Int64)
                        if new_type == 'Int64':
                            # SUB-SCENARIO A: The Rounding Problem (float -> Int64)
                            if pd.api.types.is_float_dtype(current_dtype):
                                if not rounding_method:
                                    # If it's a float and the user didn't specify rounding, add a warning and skip.
                                    code_snippets.append(f"# WARNING: Cannot convert '{col}' from float to Int64 without rounding. Please select a rounding method.")
                                    continue # Skip to the next column
                                else:
                                    # User provided rounding, so proceed.
                                    code_snippets.append(f"\n# Rounding and converting '{col}' from float to Int64")
                                    if rounding_method == 'round':
                                        df_cleaned[col] = df_cleaned[col].round()
                                        code_snippets.append(f"df['{col}'] = df['{col}'].round()")
                                    elif rounding_method == 'floor':
                                        df_cleaned[col] = np.floor(df_cleaned[col])
                                        code_snippets.append(f"df['{col}'] = np.floor(df['{col}'])")
                                    elif rounding_method == 'ceil':
                                        df_cleaned[col] = np.ceil(df_cleaned[col])
                                        code_snippets.append(f"df['{col}'] = np.ceil(df['{col}'])")
                                    
                                    df_cleaned[col] = df_cleaned[col].astype('Int64')
                                    code_snippets.append(f"df['{col}'] = df['{col}'].astype('Int64')")
                            
                            # SUB-SCENARIO B: The NaN Problem (object -> Int64)
                            else:
                                df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce').astype('Int64')
                                code_snippets.append(f"df['{col}'] = pd.to_numeric(df['{col}'], errors='coerce').astype('Int64')")

                        # SCENARIO 2: Converting TO a datetime
                        elif new_type == 'datetime64[ns]':
                            df_cleaned[col] = pd.to_datetime(df_cleaned[col], errors='coerce')
                            code_snippets.append(f"df['{col}'] = pd.to_datetime(df['{col}'], errors='coerce')")
                        
                        # SCENARIO 3: All other conversions
                        else:
                            df_cleaned[col] = df_cleaned[col].astype(new_type)
                            code_snippets.append(f"df['{col}'] = df['{col}'].astype('{new_type}')")

                    except Exception as e:
                        code_snippets.append(f"# WARNING: Could not convert '{col}' to '{new_type}': {e}")


        # --- END OF THE NEW BLOCK ---

        # ... (The "Convert Float to Integer" operation and others should remain here) ...
        float_to_int_cols = request.form.getlist('float_to_int_columns')
        rounding_method = request.form.get('rounding_method')
        if float_to_int_cols and rounding_method:
            code_snippets.append("\n# Convert float columns to integer")
            for col in float_to_int_cols:
                if col in df_cleaned.columns and pd.api.types.is_numeric_dtype(df_cleaned[col]):
                    if rounding_method == 'round':
                        df_cleaned[col] = df_cleaned[col].round()
                        code_snippets.append(f"df['{col}'] = df['{col}'].round()")
                    elif rounding_method == 'floor':
                        df_cleaned[col] = np.floor(df_cleaned[col])
                        code_snippets.append(f"df['{col}'] = np.floor(df['{col}'])")
                    elif rounding_method == 'ceil':
                        df_cleaned[col] = np.ceil(df_cleaned[col])
                        code_snippets.append(f"df['{col}'] = np.ceil(df['{col}'])")
                    
                    df_cleaned[col] = df_cleaned[col].astype('Int64')
                    code_snippets.append(f"df['{col}'] = df['{col}'].astype('Int64')")


        
        # 4. Bulk String Manipulation
        str_cols = request.form.getlist('str_columns')
        if str_cols:
            code_snippets.append("\n# String transformations")
            case_change = request.form.get('str_case')
            if case_change:
                for col in str_cols:
                    if col in df_cleaned.columns:
                        df_cleaned[col] = getattr(df_cleaned[col].str, case_change)()
                        code_snippets.append(f"df['{col}'] = df['{col}'].str.{case_change}()")
            
            if request.form.get('str_strip'):
                for col in str_cols:
                    if col in df_cleaned.columns:
                        df_cleaned[col] = df_cleaned[col].str.strip()
                        code_snippets.append(f"df['{col}'] = df['{col}'].str.strip()")

            find_val = request.form.get('str_find')
            replace_val = request.form.get('str_replace', '')
            if find_val:
                for col in str_cols:
                    if col in df_cleaned.columns:
                        df_cleaned[col] = df_cleaned[col].str.replace(find_val, replace_val)
                        code_snippets.append(f"df['{col}'] = df['{col}'].str.replace('{find_val}', '{replace_val}')")
        
        # 5. Feature Engineering (Numeric Scaling & Date Extraction)
        scale_cols = request.form.getlist('scale_columns')
        scaler_type = request.form.get('scaler_type')
        if scale_cols and scaler_type:
            scaler = StandardScaler() if scaler_type == 'standard' else MinMaxScaler()
            scaler_class_name = scaler.__class__.__name__
            code_snippets.append(f"\n# Apply {scaler_type} scaling")
            code_snippets.append(f"from sklearn.preprocessing import {scaler_class_name}")
            code_snippets.append(f"scaler = {scaler_class_name}()")
            for col in scale_cols:
                if col in df_cleaned.columns:
                    try:
                        # Create a new scaled column
                        df_cleaned[f'{col}_scaled'] = scaler.fit_transform(df_cleaned[[col]])
                        code_snippets.append(f"df['{col}_scaled'] = scaler.fit_transform(df[['{col}']])")
                    except Exception as e:
                        code_snippets.append(f"# WARNING: Could not scale '{col}': {e}")
        
        date_cols = request.form.getlist('date_columns')
        date_parts = request.form.getlist('date_parts')
        if date_cols and date_parts:
            code_snippets.append("\n# Date feature extraction")
            for col in date_cols:
                if col in df_cleaned.columns:
                    # Ensure the column is datetime before attempting extraction
                    df_cleaned[col] = pd.to_datetime(df_cleaned[col], errors='coerce')
                    for part in date_parts:
                        try:
                            # Create new columns for each part
                            df_cleaned[f'{col}_{part}'] = getattr(df_cleaned[col].dt, part)
                            code_snippets.append(f"df['{col}_{part}'] = df['{col}'].dt.{part}")
                        except Exception as e:
                             code_snippets.append(f"# WARNING: Could not extract '{part}' from '{col}': {e}")

        # 6. Categorical Encoding
        encode_cols = request.form.getlist('encode_columns')
        encoding_method = request.form.get('encoding_method')
        if encode_cols and encoding_method:
            code_snippets.append(f"\n# Apply {encoding_method} encoding")
            if encoding_method == 'one_hot':
                # One-Hot Encoding creates new columns and drops the original
                code_snippets.append(f"df = pd.get_dummies(df, columns={encode_cols}, prefix={encode_cols})")
                df_cleaned = pd.get_dummies(df_cleaned, columns=encode_cols, prefix=encode_cols)
            elif encoding_method == 'label':
                # Label Encoding creates a new column for each original column
                code_snippets.append("from sklearn.preprocessing import LabelEncoder")
                code_snippets.append("encoder = LabelEncoder()")
                for col in encode_cols:
                    if col in df_cleaned.columns:
                        try:
                            df_cleaned[f'{col}_encoded'] = LabelEncoder().fit_transform(df_cleaned[col])
                            code_snippets.append(f"df['{col}_encoded'] = encoder.fit_transform(df['{col}'])")
                        except Exception as e:
                            code_snippets.append(f"# WARNING: Could not label encode '{col}': {e}")

        checkpoints = session.get('checkpoints', [])
        checkpoint_name = request.form.get('checkpoint_name') or f"Checkpoint {len(checkpoints) + 1}"
        cleaned_filename = f"{session['session_id']}_cp{len(checkpoints)}.csv"
        df_cleaned.to_csv(get_file_path('CLEANED_FOLDER', cleaned_filename), index=False)
        
        base_cp_data = next((cp for cp in checkpoints if cp['filename'] == base_checkpoint_file), None)
        base_code = base_cp_data['full_code'] if base_cp_data else ""
        full_code = base_code + "".join(code_snippets)
        
        checkpoints.append({'name': checkpoint_name, 'filename': cleaned_filename, 'full_code': full_code})
        session['checkpoints'] = checkpoints
        return redirect(url_for('main.workspace'))

    checkpoints = session.get('checkpoints', [])
    latest_checkpoint_data = checkpoints[-1]
    return render_template('workspace.html', checkpoints=checkpoints, initial_data=latest_checkpoint_data)


@main_bp.route('/api/checkpoint_details/<path:filename>')
def get_checkpoint_details(filename):
    if 'checkpoints' not in session: return jsonify({'error': 'No session found'}), 404
    checkpoint_data = next((cp for cp in session['checkpoints'] if cp['filename'] == filename), None)
    if not checkpoint_data: return jsonify({'error': 'Checkpoint not found'}), 404
    df_path = get_file_path('CLEANED_FOLDER', filename)
    if not os.path.exists(df_path): return jsonify({'error': 'Checkpoint file not found'}), 404
    
    # Step 1: Read the CSV. Pandas will likely infer Int64 columns as float64.
    df = pd.read_csv(df_path, low_memory=False)
    
    # Step 2: Use the code history as the "source of truth" to re-apply conversions.
    full_code = checkpoint_data['full_code']
    for col in df.columns:
        # Check if the cumulative code contains the specific Int64 conversion command for this column.
        if f"df['{col}'] = df['{col}'].astype('Int64')" in full_code:
            try:
                df[col] = df[col].astype('Int64')
            except (ValueError, TypeError): pass # Failsafe
            
        # Also check for datetime conversions
        if f"df['{col}'] = pd.to_datetime(df['{col}'], errors='coerce')" in full_code:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Step 3: Generate response data from the CORRECTED DataFrame
    response_data = {
        'name': checkpoint_data['name'], 'full_code': checkpoint_data['full_code'],
        'head_html': df.head().to_html(classes='table table-striped table-sm', index=False, border=0),
        'info_html': get_df_info(df), 'columns': df.columns.tolist(),
        'numeric_cols': df.select_dtypes(include=['number']).columns.tolist(),
        'categorical_cols': df.select_dtypes(include=['object', 'category']).columns.tolist(),
        'datetime_cols': df.select_dtypes(include=['datetime']).columns.tolist()
    }
    return jsonify(response_data)


@main_bp.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(current_app.config['CLEANED_FOLDER'], filename, as_attachment=True)
