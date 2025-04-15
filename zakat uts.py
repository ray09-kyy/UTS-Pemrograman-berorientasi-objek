import pandas as pd
import mysql.connector
from datetime import datetime
from mysql.connector import Error
from decimal import Decimal

## ==============================================
## DATABASE INITIALIZATION FUNCTIONS
## ==============================================

def create_connection():
    """Membuat koneksi ke database MySQL"""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="db_zakat"
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def check_database_exists():
    """Memeriksa apakah database ada, jika tidak akan dibuat"""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conn.cursor()
        
        cursor.execute("SHOW DATABASES LIKE 'db_zakat'")
        result = cursor.fetchone()
        
        if not result:
            cursor.execute("CREATE DATABASE db_zakat CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("Database 'db_zakat' berhasil dibuat")
        
        cursor.close()
        conn.close()
        return True
        
    except Error as e:
        print(f"Error checking/creating database: {e}")
        return False

def create_tables():
    """Membuat tabel-tabel yang diperlukan jika belum ada"""
    conn = create_connection()
    if conn is None:
        print("Cannot create tables without database connection")
        return False
    
    create_table_queries = [
        """
        CREATE TABLE IF NOT EXISTS transaksi_zakat (
            id INT AUTO_INCREMENT PRIMARY KEY,
            jenis_zakat VARCHAR(20) NOT NULL,
            nominal DECIMAL(15, 2) NOT NULL,
            nama_pembayar VARCHAR(100) NOT NULL,
            tanggal DATE NOT NULL,
            metode_pembayaran VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS config (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nisab_emas DECIMAL(10, 2) DEFAULT 85.0,
            zakat_fitrah_beras DECIMAL(10, 2) DEFAULT 2.5,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    ]
    
    cursor = None
    try:
        cursor = conn.cursor()
        
        for query in create_table_queries:
            cursor.execute(query)
        
        cursor.execute("SELECT COUNT(*) FROM config")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO config (nisab_emas, zakat_fitrah_beras) VALUES (85.0, 2.5)")
        
        conn.commit()
        print("Tabel berhasil dibuat/diverifikasi")
        return True
        
    except Error as e:
        print(f"Error creating tables: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def initialize_database():
    """Fungsi utama untuk inisialisasi database dan tabel"""
    print("Memeriksa database dan tabel...")
    
    if not check_database_exists():
        return False
    
    if not create_tables():
        return False
    
    return True

## ==============================================
## UTILITY FUNCTIONS
## ==============================================

def get_numeric_input(prompt, min_value=0):
    """Validasi input numerik dan mengembalikan Decimal"""
    while True:
        try:
            value = Decimal(input(prompt))
            if value >= Decimal(str(min_value)):
                return value
            print(f"Input must be greater than or equal to {min_value}")
        except ValueError:
            print("Please enter a valid number.")

def get_non_empty_input(prompt):
    """Validasi input string tidak kosong"""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field cannot be empty.")

def get_config_value(key):
    """Mengambil nilai konfigurasi dari database sebagai Decimal"""
    conn = create_connection()
    if conn is None:
        return None
    
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT {key} FROM config LIMIT 1")
        result = cursor.fetchone()
        return Decimal(str(result[key])) if result else None
    except Error as e:
        print(f"Error getting config value: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

## ==============================================
## ZAKAT CALCULATION FUNCTIONS
## ==============================================

def hitung_zakat_maal():
    print("\n=== Menghitung Zakat Maal (2.5% dari Harta) ===")
    try:
        nama = get_non_empty_input("Nama Pembayar: ")
        total_harta = get_numeric_input("Total harta (dalam mata uang lokal): ", 0)
        
        nisab_emas = get_config_value('nisab_emas') or Decimal('85.0')
        harga_emas_per_gram = get_numeric_input("Harga emas per gram saat ini: ", 0)
        nisab_harga = nisab_emas * harga_emas_per_gram

        if total_harta >= nisab_harga:
            zakat = total_harta * Decimal('0.025')
            print(f"\nAnda wajib membayar zakat maal sebesar: {zakat:,.2f}")
            
            while True:
                metode = get_non_empty_input("Metode pembayaran (Tunai/Transfer): ").capitalize()
                if metode in ['Tunai', 'Transfer']:
                    break
                print("Please enter either 'Tunai' or 'Transfer'")

            conn = create_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    query = """
                    INSERT INTO transaksi_zakat (jenis_zakat, nominal, nama_pembayar, tanggal, metode_pembayaran)
                    VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(query, ('maal', float(zakat), nama, datetime.now().date(), metode))
                    conn.commit()
                    print("Data zakat maal berhasil disimpan!")
                except Error as e:
                    print(f"Error saving to database: {e}")
                    conn.rollback()
                finally:
                    conn.close()
        else:
            print(f"\nAnda belum mencapai nisab (Nisab saat ini: {nisab_harga:,.2f})")
    except Exception as e:
        print(f"An error occurred: {e}")

def hitung_zakat_fitrah():
    print("\n=== Menghitung Zakat Fitrah ===")
    try:
        nama = get_non_empty_input("Nama Pembayar: ")
        jumlah_jiwa = int(get_numeric_input("Jumlah jiwa: ", 1))
        harga_beras_per_kg = get_numeric_input("Harga beras per kg: ", 0)
        
        zakat_per_jiwa = get_config_value('zakat_fitrah_beras') or Decimal('2.5')
        total_zakat = jumlah_jiwa * zakat_per_jiwa * harga_beras_per_kg
        print(f"\nTotal zakat fitrah: {total_zakat:,.2f}")
        
        while True:
            metode = get_non_empty_input("Metode pembayaran (Tunai/Transfer): ").capitalize()
            if metode in ['Tunai', 'Transfer']:
                break
            print("Please enter either 'Tunai' or 'Transfer'")

        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                query = """
                INSERT INTO transaksi_zakat (jenis_zakat, nominal, nama_pembayar, tanggal, metode_pembayaran)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(query, ('fitrah', float(total_zakat), nama, datetime.now().date(), metode))
                conn.commit()
                print("Data zakat fitrah berhasil disimpan!")
            except Error as e:
                print(f"Error saving to database: {e}")
                conn.rollback()
            finally:
                conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")

## ==============================================
## REPORT FUNCTION
## ==============================================

def lihat_laporan():
    try:
        conn = create_connection()
        if conn:
            try:
                query = """
                SELECT id, jenis_zakat, 
                       CONCAT('Rp', FORMAT(nominal, 2)) as nominal, 
                       nama_pembayar, 
                       DATE_FORMAT(tanggal, '%d-%m-%Y') as tanggal, 
                       metode_pembayaran
                FROM transaksi_zakat
                ORDER BY tanggal DESC
                """
                df = pd.read_sql(query, conn)
                
                if df.empty:
                    print("\nBelum ada data transaksi zakat.")
                else:
                    print("\n=== Laporan Transaksi Zakat ===")
                    print(df.to_string(index=False))
            except Error as e:
                print(f"Error retrieving data: {e}")
            finally:
                conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")

## ==============================================
## MAIN MENU
## ==============================================

def main():
    if not initialize_database():
        print("Tidak dapat melanjutkan karena masalah database")
        return
    
    while True:
        try:
            print("\n=== Aplikasi Pembayaran Zakat ===")
            print("1. Hitung Zakat Maal")
            print("2. Hitung Zakat Fitrah")
            print("3. Lihat Laporan Transaksi")
            print("4. Keluar")
            
            pilihan = input("Pilih menu (1/2/3/4): ").strip()
            
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
                print("Pilihan tidak valid! Silakan pilih 1-4.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            print("Please try again.")

if __name__ == "__main__":
    main()