
from flask import Flask, request, render_template, send_file
import pandas as pd
import io

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            file = request.files['excel_file']
            islem = request.form.get("islem_turu")

            if not file or not islem:
                return "Dosya veya işlem türü seçilmedi."

            df = pd.read_excel(file)

            if islem == "avantajli":
                df = avantajli_indirim_hesapla(df)
            elif islem == "komisyon":
                df = komisyon_tsf_hesapla(df)
            else:
                return "Geçersiz işlem türü."

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            output.seek(0)

            return send_file(output, as_attachment=True,
                             download_name="sonuc.xlsx",
                             mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        except Exception as e:
            return f"Hata oluştu: {str(e)}"

    return render_template("index.html")


def avantajli_indirim_hesapla(df):
    try:
        if "TRENDYOL SATIŞ FİYATI" in df.columns and "MÜŞTERİNİN GÖRDÜĞÜ FİYAT" in df.columns:
            tf = df["TRENDYOL SATIŞ FİYATI"]
            gf = df["MÜŞTERİNİN GÖRDÜĞÜ FİYAT"]
            yeni_tsf = tf * 0.9
            indirim = (tf - yeni_tsf).round(2)

            df["YENİ TSF"] = yeni_tsf
            df["İNDİRİM TUTARI"] = indirim
    except Exception as e:
        df["HATA"] = f"Avantajlı hesaplama hatası: {str(e)}"
    return df


def komisyon_tsf_hesapla(df):
    try:
        if "GÜNCEL TSF" in df.columns and "KOMİSYONA ESAS FİYAT" in df.columns:
            indirim_yuzde = 1 - (df["KOMİSYONA ESAS FİYAT"] / df["GÜNCEL TSF"])
            indirim_yuzde = indirim_yuzde.fillna(0).clip(lower=0)
            df["İndirim (%)"] = (indirim_yuzde * 100).round(0)

            hedef_esas = df.get("1.Fiyat Alt Limit", pd.Series([0]*len(df))) + 1
            yeni_tsf = hedef_esas / (1 - indirim_yuzde)
            df["Yeni TSF (1. Komisyon)"] = yeni_tsf.round(2)
    except Exception as e:
        df["HATA"] = f"Komisyon hesaplama hatası: {str(e)}"
    return df
