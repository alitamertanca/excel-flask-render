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
        gerekli_sutunlar = [
            "GÜNCEL TSF", "KOMİSYONA ESAS FİYAT", "GÜNCEL KOMİSYON",
            "1.Fiyat Alt Limit", "2.Fiyat Üst Limiti", "3.Fiyat Üst Limiti", "4.Fiyat Üst Limiti",
            "2.KOMİSYON", "3.KOMİSYON", "4.KOMİSYON"
        ]
        for s in gerekli_sutunlar:
            if s not in df.columns:
                raise Exception(f"Gerekli sütun eksik: {s}")

        # Yeni sütunlar
        df["İndirim (%)"] = np.nan
        for j in range(1, 5):
            df[f"YeniTSF ({j}. Komisyon)"] = np.nan
            df[f"Fark({j}. Komisyon)"] = ""

        # Satır bazlı hızlı ve adlarla işlem
        for idx, (
            tsf, esas_fiyat, guncel_komisyon,
            alt_limit, ust2, ust3, ust4,
            kom2, kom3, kom4
        ) in df[[
            "GÜNCEL TSF", "KOMİSYONA ESAS FİYAT", "GÜNCEL KOMİSYON",
            "1.Fiyat Alt Limit", "2.Fiyat Üst Limiti", "3.Fiyat Üst Limiti", "4.Fiyat Üst Limiti",
            "2.KOMİSYON", "3.KOMİSYON", "4.KOMİSYON"
        ]].itertuples(index=True, name=None):

            try:
                tsf = float(tsf)
                esas_fiyat = float(esas_fiyat)
                guncel_komisyon = float(guncel_komisyon)

                fiyat_limitleri = [float(alt_limit), float(ust2), float(ust3), float(ust4)]
                komisyonlar = [guncel_komisyon, float(kom2), float(kom3), float(kom4)]

                indirim_orani = 0 if tsf == 0 else 1 - (esas_fiyat / tsf)
                df.at[idx, "İndirim (%)"] = round(indirim_orani * 100, 2)

                for j in range(1, 5):
                    hedef_fiyat = (fiyat_limitleri[j - 1] + 1) if j == 1 else (fiyat_limitleri[j - 1] - 1)
                    yeni_tsf = round(hedef_fiyat / (1 - indirim_orani), 2)
                    fark = round(yeni_tsf - tsf, 2)

                    if j == 1 or guncel_komisyon != komisyonlar[j - 1]:
                        df.at[idx, f"YeniTSF ({j}. Komisyon)"] = yeni_tsf
                        df.at[idx, f"Fark({j}. Komisyon)"] = fark
                    else:
                        df.at[idx, f"YeniTSF ({j}. Komisyon)"] = tsf
                        df.at[idx, f"Fark({j}. Komisyon)"] = f"Güncel Komisyon: {guncel_komisyon}"

            except Exception as satir_hatasi:
                df.at[idx, "HATA"] = f"Satır hatası: {satir_hatasi}"

    except Exception as e:
        df["HATA"] = f"Genel komisyon hesaplama hatası: {str(e)}"

    return df
