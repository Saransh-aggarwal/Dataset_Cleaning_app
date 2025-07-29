import pandas as pd
import io

def get_df_info(df):
    buffer = io.StringIO()
    df.info(buf=buffer)
    return buffer.getvalue()

def read_file(filepath):
  
    try:
        if filepath.endswith('.csv'):
            return pd.read_csv(filepath, low_memory=False)
        else:
            return pd.read_excel(filepath)
    except Exception as e:
        
        print(f"Error reading file {filepath}: {e}")
        
        return None