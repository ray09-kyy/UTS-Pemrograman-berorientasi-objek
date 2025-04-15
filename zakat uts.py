import pandas as pd
import mysql.connector
from datetime import datetime

# Koneksi ke MySQL
def create_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",  # Ganti dengan username MySQL Anda
        password="",  # Ganti dengan password MySQL Anda
        database="db_zakat"
    )
    return conn

# Menghitung Zakat Maal (2.5% dari harta)
def hitung_zakat_maal():
    print("\n=== Menghitung Zakat Maal (2.5% dari Harta) ===")
    nama = input("Nama Pembayar: ")
    total_harta = float(input("Total harta (dalam mata uang lokal): "))
    nisab_emas = 85  # gram
    harga_emas_per_gram = float(input("Harga emas per gram saat ini: "))
    nisab_harga = nisab_emas * harga_emas_per_gram

    if total_harta >= nisab_harga:
        zakat = total_harta * 0.025
        print(f"\nAnda wajib membayar zakat maal sebesar: {zakat:.2f}")
        metode = input("Metode pembayaran (Tunai/Transfer): ")
        
        # Simpan ke database
        conn = create_connection()
        cursor = conn.cursor()
        query = """
        INSERT INTO transaksi_zakat (jenis_zakat, nominal, nama_pembayar, tanggal, metode_pembayaran)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, ('maal', zakat, nama, datetime.now().date(), metode))
        conn.commit()
        conn.close()
        print("Data zakat maal berhasil disimpan!")
    else:
        print(f"\nAnda belum mencapai nisab (Nisab saat ini: {nisab_harga:.2f})")

# Menghitung Zakat Fitrah (2.5 kg beras atau setara)
def hitung_zakat_fitrah():
    print("\n=== Menghitung Zakat Fitrah ===")
    nama = input("Nama Pembayar: ")
    jumlah_jiwa = int(input("Jumlah jiwa: "))
    harga_beras_per_kg = float(input("Harga beras per kg: "))
    zakat_per_jiwa = 2.5  # kg
    total_zakat = jumlah_jiwa * zakat_per_jiwa * harga_beras_per_kg
    print(f"\nTotal zakat fitrah: {total_zakat:.2f}")
    metode = input("Metode pembayaran (Tunai/Transfer): ")

    # Simpan ke database
    conn = create_connection()
    cursor = conn.cursor()
    query = """
    INSERT INTO transaksi_zakat (jenis_zakat, nominal, nama_pembayar, tanggal, metode_pembayaran)
    VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, ('fitrah', total_zakat, nama, datetime.now().date(), metode))
    conn.commit()
    conn.close()
    print("Data zakat fitrah berhasil disimpan!")

# Menampilkan Laporan Zakat dalam DataFrame
def lihat_laporan():
    conn = create_connection()
    query = "SELECT * FROM transaksi_zakat"
    df = pd.read_sql(query, conn)
    conn.close()

    if df.empty:
        print("\nBelum ada data transaksi zakat.")
    else:
        print("\n=== Laporan Transaksi Zakat ===")
        print(df)

# Menu Utama
def main():
    print("\n=== Aplikasi Pembayaran Zakat ===")
    print("1. Hitung Zakat Maal")
    print("2. Hitung Zakat Fitrah")
    print("3. Lihat Laporan Transaksi")
    print("4. Keluar")

    while True:
        pilihan = input("\nPilih menu (1/2/3/4): ")

        if pilihan == '1':
            hitung_zakat_maal()
        elif pilihan == '2':
            hitung_zakat_fitrah()
        elif pilihan == '3':
            lihat_laporan()
        elif pilihan == '4':
            print("Terima kasih. Semoga amal ibadah Anda diterima.")
            break
        else:
            print("Pilihan tidak valid!")

if __name__ == "__main__":
    main()