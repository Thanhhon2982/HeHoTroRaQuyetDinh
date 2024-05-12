from flask import Flask, render_template, request, send_from_directory
import pandas as pd
import numpy as np
import tkinter as tk
import json 
from tkinter import filedialog 
app = Flask(__name__)


@app.route('/')
def home():
    return render_template('gioithieu.html')

@app.route('/phuongan')
def phuongan():
    return render_template('phuongan.html')

@app.route('/trongso')
def trongso():
    return render_template('trongso.html')


@app.route('/calculate', methods=['POST'])
def calculate():
    matrix_data = request.form['matrixData']
    matrix = np.array(json.loads(matrix_data))
   
    # Khởi tạo DataFrame df từ dữ liệu ma trận
    df = pd.DataFrame(matrix)
    
    # Thực hiện các phép toán tính toán trên ma trận
    column_sums = np.sum(matrix, axis=0)
    sum_row = pd.DataFrame([column_sums], columns=df.columns, index=['Sum'])
    df = pd.concat([df, sum_row])
    headerRowData = request.form.getlist('matrixHeaders')
    headers = headerRowData
    df.columns = headers
    df = df.rename(index={i: header for i, header in enumerate(headers)})
    genuine_df = df.copy()
    df = df.rename(index={df.index[-1]: 'Sum'})
    normalized_matrix = df.div(df.iloc[:-1].sum(axis=0), axis=1)
    avg = normalized_matrix.mean(axis=1)
    new_df = pd.concat([normalized_matrix, avg.rename('Average')], axis=1)
    save_normalized_matrix(new_df['Average'].iloc[:-1])
    cr_df = genuine_df.copy()
    avg = [list(row)[-1] for _, row in new_df.iterrows()][:-1]
    cr_df = cr_df.mul(avg, axis=1)
    crc_df = cr_df.copy()
    crc_df = pd.concat([crc_df, crc_df.sum(axis=1).rename('Weighted sum'), new_df.iloc[:, -1:]], axis=1).rename(columns={'Average': 'Criteria weights'})
    vector = crc_df.iloc[:, -2:-1]['Weighted sum'].div(crc_df.iloc[:, -1:]['Criteria weights'])
    crc_df = pd.concat([crc_df, vector.rename('Consistency vector')], axis=1)
    lambda_max = vector[:-1].sum() / (len(vector) - 1)
    ci = (lambda_max - 5) / (5 - 1)
    cr = ci / 1.12
    cr_df = cr_df.drop('Sum')
    crc_df = crc_df.drop('Sum')
    normalized_matrix = new_df.drop('Sum')
    html_table_1 = df.round(4).to_html(index=True)
    html_table_2 = normalized_matrix.round(4).to_html(index=True)
    html_table_3 = cr_df.round(4).to_html(index=True)
    html_table_4 = crc_df.round(4).to_html(index=True)

    return render_template('resultTS.html',
                           table_1=html_table_1,
                           table_2=html_table_2,
                           table_3=html_table_3,
                           table_4=html_table_4,
                           lambda_max=lambda_max,
                           ci=ci,
                           cr=cr)

def unified_compute1():
    matrix_data = request.form['matrixData']
    matrix = np.array(json.loads(matrix_data))
    
    # Khởi tạo DataFrame df từ dữ liệu ma trận
    df = pd.DataFrame(matrix)
    
    column_sums = np.sum(df, axis=0)

    undisturbed = df.iloc()[:]
    divided = np.divide(df.iloc()[:], column_sums)

    sum_row = pd.DataFrame([column_sums], columns=df.columns, index=['Sum'])
    df = pd.concat([df, sum_row])
    headers = ['Bệnh Viện ĐH Y Dược', 'Bệnh Viện Chợ Rẫy', 'Bệnh Viện Nhi Đồng 1', 'Bệnh Viện Nhân Dân 115']
    df.columns = headers
    undisturbed.columns = headers
    divided.columns = headers

    df = df.rename(index={i: header for i, header in enumerate(headers)})
    undisturbed = undisturbed.rename(index={i: header for i, header in enumerate(headers)})
    divided = divided.rename(index={i: header for i, header in enumerate(headers)})

    sum_df = df.iloc()[:]
    # genuine_df = df.iloc()[:-1]

    avg = divided.mean(axis=1).rename('Trọng số P.A')
    save_normalized_matrix(avg)
    df = pd.concat([divided, avg], axis=1)
    weighted_df = df.iloc()[:]

    df = undisturbed.iloc()[:].mul(avg, axis=1)
    new_columns = [df.sum(axis=1).rename('Sum Weight'), avg.rename('Trọng số')]
    cv = new_columns[0].div(new_columns[1])
    df = pd.concat(
        [df, new_columns[0], new_columns[1], cv.rename('Consistency vector')], axis=1)
    cv_df = df.iloc()[:]
    lambda_max = cv.mean()
    ci = (lambda_max - 4) / 3
    cr = ci / 0.9

    return {
        'sum_df': sum_df,
        'weighted_df': weighted_df,
        'cv_df': cv_df,
        'lambda_max': lambda_max,
        'ci': ci,
        'cr': cr
    }
Phuongan = {
    'title': 'Tính Phương án ',
    'label_1': 'TÍNH TỔNG',
    'label_2': 'TRỌNG SỐ P.A',
    'label_3': 'CONSISTENCY VECTOR',
    'cr_bound': 0.9
}



def unified_output1(lookup):
    excel_file = request.form['matrixData']  # Thêm tên trường 'excel_file' vào request.files
    if excel_file:
        results = unified_compute1()  
        return render_template('resultPA.html',
                               title=lookup['title'],
                               label_1=lookup['label_1'],
                               table_1=results['sum_df'].round(4).to_html(index=True),
                               label_2=lookup['label_2'],
                               table_2=results['weighted_df'].round(4).to_html(index=True),
                               label_3=lookup['label_3'],
                               table_3=results['cv_df'].round(4).to_html(index=True),
                               lambda_max=results['lambda_max'],
                               ci=results['ci'],
                               cr=results['cr'],
                               cr_bound=lookup['cr_bound'])
    else:
        return "No file uploaded."


@app.route('/calculate1', methods=['POST'])
def calculate1():
    return unified_output1(Phuongan) 

def save_normalized_matrix(normalized_matrix):
    root = tk.Tk()
    root.withdraw()
    
    def save_file():
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")]) 
        if file_path:
            try:
                normalized_matrix.to_excel(file_path, header=False, index=False, engine='openpyxl')
                print("Normalized matrix saved to:", file_path)
            except Exception as e:
                print("Error:", e)
        else:
            print("No file selected.")
        root.destroy()  # Đóng cửa sổ sau khi hoàn thành lưu file
    
    root.after(0, save_file)  # Thực hiện lưu file trong vòng lặp chính của tkinter

    root.mainloop()  # Khởi động vòng lặp chính của tkinter


@app.route('/tinh2matran')
def tinh2matran():
    return render_template('tinh2matran.html')

@app.route('/chontep', methods=['POST'])
def chontep():
    excel_file_1 = request.files['excel_file_1']
    
    html_table_1 = ""
    html_table_2 = ""
    
    if excel_file_1:
        # Đọc dữ liệu từ tệp Excel 1 và chuyển thành HTML table
        df_1 = pd.read_excel(excel_file_1, header=None)
        html_table_1 = df_1.to_html(index=False, header=None)

    # Lấy danh sách các file từ request
    excel_files = request.files.getlist('excel_files')
    
    combined_df = pd.DataFrame()
    
    # Lặp qua từng file
    for file in excel_files:
        # Đọc dữ liệu từ từng tệp Excel và nối theo hàng ngang vào DataFrame chính
        if file:
            df_2 = pd.read_excel(file, header=None)
            combined_df = pd.concat([combined_df, df_2], axis=1)  # Nối theo hàng ngang
    
    # Chuyển DataFrame thành HTML table
    html_table_2 = combined_df.to_html(index=False, header=None)

    # Trả về trang HTML chứa cả hai bảng
    return render_template('result2mt.html', html_table_1=html_table_1, html_table_2=html_table_2)

def multiply_matrices(matrix1, matrix2):
    # Chuyển các ma trận từ chuỗi HTML thành DataFrame
    df1 = pd.read_html(matrix1, header=None)[0]
    df2 = pd.read_html(matrix2, header=None)[0]
    
    # Chuyển DataFrame thành ma trận
    mat1 = df1.values
    mat2 = df2.values
    print(mat1)
    print(mat2)
    # Thực hiện phép nhân ma trận
    result = np.dot(mat2, mat1)
    
    # Chuyển ma trận kết quả thành DataFrame
    result_df = pd.DataFrame(result)
    
    # Chuyển DataFrame thành chuỗi HTML
    result_html = result_df.to_html(index=False,header=None)
    
    return result_html

@app.route('/multiply_matrices', methods=['POST'])
def multiply_matrices_route():
    html_table_1 = request.form['matrix_data_1']
    html_table_2 = request.form['matrix_data_2']
    
    # Thực hiện phép nhân ma trận
    result_html = multiply_matrices(html_table_1, html_table_2)
    
    return render_template('travekq.html', result_html=result_html)

if __name__ == "__main__":
    app.run(debug=True)
