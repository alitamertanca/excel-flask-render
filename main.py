
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
                 df.to_excel(writer, index=False, sheet_name="YıldızlıÜrünEtiketleri")
            output.seek(0)

            return send_file(output, as_attachment=True,
                             download_name="avantajli_urun_sonuclar.xlsx",
                             mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        except Exception as e:
            return f"Hata oluştu: {str(e)}"

    return render_template("index.html")


def avantajli_indirim_hesapla(df):
    try:
        def temiz_sayi(deger):
            try:
                return float(str(deger).replace(".", "").replace(",", "."))
            except:
                return 0

        t_sonuclar, u_kaynak, yeni_tsf = [], [], []

        for i in df.index:
            try:
                tf = temiz_sayi(df.at[i, "TRENDYOL SATIŞ FİYATI"])
                gf = temiz_sayi(df.at[i, "MÜŞTERİNİN GÖRDÜĞÜ FİYAT"])
                y1Ust = temiz_sayi(df.at[i, "1 YILDIZ ÜST FİYAT"])
                y2Ust = temiz_sayi(df.at[i, "2 YILDIZ ÜST FİYAT"])
                y3Ust = temiz_sayi(df.at[i, "3 YILDIZ ÜST FİYAT"])

                if tf == 0 or gf == 0:
                    t_sonuclar.append("")
                    u_kaynak.append("")
                    yeni_tsf.append("")
                    continue

                if gf > y1Ust:
                    hedefGF, kaynak = y1Ust, "1 YILDIZ ÜST FİYAT"
                elif gf > y2Ust:
                    hedefGF, kaynak = y2Ust, "2 YILDIZ ÜST FİYAT"
                elif gf > y3Ust:
                    hedefGF, kaynak = y3Ust, "3 YILDIZ ÜST FİYAT"
                else:
                    t_sonuclar.append(0)
                    u_kaynak.append("En iyi fiyatta")
                    yeni_tsf.append(tf)
                    continue

                hedef_fiyat = tf * (hedefGF / gf)
                indirim_tl = max(0, round(tf - hedef_fiyat, 2))

                t_sonuclar.append(indirim_tl)
                u_kaynak.append(kaynak)
                yeni_tsf.append(round(tf - indirim_tl, 2))

            except:
                t_sonuclar.append("")
                u_kaynak.append("")
                yeni_tsf.append("")

        df["TRENDYOL İndirim Tutarı"] = t_sonuclar
        df["İNDİRİM KAYNAK FİYAT"] = u_kaynak
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
