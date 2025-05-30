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
        # Gerekli sütunlar
        gerekli_sutunlar = [
            "GÜNCEL TSF", "KOMİSYONA ESAS FİYAT", "GÜNCEL KOMİSYON",
            "1.Fiyat Alt Limit", "2.Fiyat Üst Limiti", "3.Fiyat Üst Limiti", "4.Fiyat Üst Limiti",
            "2.KOMİSYON", "3.KOMİSYON", "4.KOMİSYON"
        ]
        for s in gerekli_sutunlar:
            if s not in df.columns:
                raise Exception(f"Gerekli sütun eksik: {s}")

        # Sayısal dönüşüm (bozuk hücreler varsa NaN olur)
        for col in gerekli_sutunlar:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # İndirim oranı hesapla
        df["İndirim (%)"] = ((1 - df["KOMİSYONA ESAS FİYAT"] / df["GÜNCEL TSF"]) * 100).round(2)
        df["İndirim (%)"] = df["İndirim (%)"].fillna(0)

        # Yeni TSF ve Fark sütunlarını vektörel hesapla
        for j in range(1, 5):
            if j == 1:
                hedef_fiyat = df["1.Fiyat Alt Limit"] + 1
            else:
                hedef_fiyat = df[f"{j}.Fiyat Üst Limiti"] - 1

            indirim_orani = 1 - df["KOMİSYONA ESAS FİYAT"] / df["GÜNCEL TSF"]
            yeni_tsf = (hedef_fiyat / (1 - indirim_orani)).round(2)
            fark = (yeni_tsf - df["GÜNCEL TSF"]).round(2)

            # Güncel komisyonla aynıysa yorum ekle
            if j == 1:
                durum_maskesi = pd.Series([True] * len(df))
            else:
                durum_maskesi = df["GÜNCEL KOMİSYON"] != df[f"{j}.KOMİSYON"]

            df[f"YeniTSF ({j}. Komisyon)"] = df["GÜNCEL TSF"]
            df[f"Fark({j}. Komisyon)"] = f"Güncel Komisyon: " + df["GÜNCEL KOMİSYON"].astype(str)

            df.loc[durum_maskesi, f"YeniTSF ({j}. Komisyon)"] = yeni_tsf
            df.loc[durum_maskesi, f"Fark({j}. Komisyon)"] = fark

    except Exception as e:
        df["HATA"] = f"Komisyon hesaplama hatası: {str(e)}"

    return df
