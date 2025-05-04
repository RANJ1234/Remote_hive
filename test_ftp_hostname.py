import ftplib
import sys
import getpass

# FTP credentials
FTP_HOST = "blue-flamingo-576401.hostingersite.com"  # Using hostname instead of IP
FTP_USERNAME = "u231309170.blue-flamingo-576401.hostingersite.com"

def test_connection():
    print(f"Attempting to connect to FTP server: {FTP_HOST}")
    print(f"Username: {FTP_USERNAME}")
    
    # Get password securely
    FTP_PASSWORD = getpass.getpass("Enter your FTP password: ")
    
    try:
        # Try to connect
        print("Establishing connection...")
        ftp = ftplib.FTP(FTP_HOST)
        print("Connection established, attempting login...")
        
        # Try to login
        ftp.login(user=FTP_USERNAME, passwd=FTP_PASSWORD)
        print("Login successful!")
        
        # List directories
        print("\nDirectory listing:")
        files = ftp.nlst()
        for file in files:
            print(f"  {file}")
        
        # Close connection
        ftp.quit()
        print("Connection closed successfully")
        return True
        
    except ftplib.all_errors as e:
        print(f"FTP Error: {e}")
        return False

if __name__ == "__main__":
    test_connection()
