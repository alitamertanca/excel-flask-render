
from flask import Flask, request, render_template, send_file
import pandas as pd
import numpy as np
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
        # Gerekli sütunları sayısal hale getir
        tf = pd.to_numeric(df["TRENDYOL SATIŞ FİYATI"], errors="coerce")
        gf = pd.to_numeric(df["MÜŞTERİNİN GÖRDÜĞÜ FİYAT"], errors="coerce")
        y1Ust = pd.to_numeric(df["1 YILDIZ ÜST FİYAT"], errors="coerce")
        y1Alt = pd.to_numeric(df["1 YILDIZ ALT FİYAT"], errors="coerce")
        y2Ust = pd.to_numeric(df["2 YILDIZ ÜST FİYAT"], errors="coerce")
        y2Alt = pd.to_numeric(df["2 YILDIZ ALT FİYAT"], errors="coerce")
        y3Ust = pd.to_numeric(df["3 YILDIZ ÜST FİYAT"], errors="coerce")

        kaynak_baslik = []
        indirimTL = []
        yeni_tsf = []

        for i in range(len(df)):
            try:
                if tf[i] == 0 or gf[i] == 0 or pd.isna(tf[i]) or pd.isna(gf[i]):
                    kaynak_baslik.append("")
                    indirimTL.append("")
                    yeni_tsf.append("")
                    continue

                if gf[i] > y1Ust[i]:
                    hedefGF = y1Ust[i]
                    kaynak = "1 YILDIZ ÜST FİYAT"
                elif gf[i] > y2Ust[i]:
                    hedefGF = y2Ust[i]
                    kaynak = "2 YILDIZ ÜST FİYAT"
                elif gf[i] > y3Ust[i]:
                    hedefGF = y3Ust[i]
                    kaynak = "3 YILDIZ ÜST FİYAT"
                else:
                    kaynak_baslik.append("")
                    indirimTL.append("En iyi fiyatta")
                    yeni_tsf.append(tf[i])
                    continue

                hedefFiyat = tf[i] * (hedefGF / gf[i]) - 0.2

                if hedefFiyat >= tf[i]:
                    indirim = 0
                else:
                    indirim = round((tf[i] - hedefFiyat) / 100, 2)

                kaynak_baslik.append(kaynak)
                indirimTL.append(indirim)
                yeni_tsf.append(round(tf[i] - indirim, 2))
            except:
                kaynak_baslik.append("HATA")
                indirimTL.append("HATA")
                yeni_tsf.append("HATA")

        df["İNDİRİM KAYNAK FİYAT"] = kaynak_baslik
        df["TRENDYOL İndirim Tutarı"] = indirimTL
        df["YENİ TSF (FİYAT GÜNCELLE)"] = yeni_tsf

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
