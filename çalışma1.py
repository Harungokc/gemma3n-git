#!/usr/bin/env python3
"""
AI Geliştirici Asistanı - Gemma 3 ile Entegre Terminal Uygulaması
"""

import os
import sys
import subprocess
import json
import requests
from pathlib import Path
import shutil
from typing import Dict, List, Optional


class AIDevAssistant:
    def __init__(self):
        self.project_config_file = ".ai_dev_config.json"
        self.project_config = self.load_project_config()
        self.data_science_libraries = [
            "pandas", "numpy", "matplotlib", "seaborn", "scikit-learn",
            "jupyter", "plotly", "scipy", "statsmodels", "openpyxl"
        ]

    def load_project_config(self) -> Dict:
        """Proje konfigürasyonunu yükle"""
        if os.path.exists(self.project_config_file):
            try:
                with open(self.project_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_project_config(self):
        """Proje konfigürasyonunu kaydet"""
        with open(self.project_config_file, 'w', encoding='utf-8') as f:
            json.dump(self.project_config, f, indent=2, ensure_ascii=False)

    def execute_command(self, command: str) -> tuple:
        """Sistem komutunu çalıştır"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def create_python_file(self, filename: str, content: str = None) -> bool:
        """Python dosyası oluştur"""
        try:
            if not filename.endswith('.py'):
                filename += '.py'

            if content is None:
                if filename == 'app.py':
                    content = '''#!/usr/bin/env python3
"""
Veri Analizi Uygulaması
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def main():
    """Ana fonksiyon"""
    print("Veri Analizi Uygulaması Başlatıldı!")

    # Örnek veri seti oluştur
    data = {
        'tarih': pd.date_range('2024-01-01', periods=100),
        'satış': np.random.randint(100, 1000, 100),
        'kategori': np.random.choice(['A', 'B', 'C'], 100),
        'müşteri_puanı': np.random.uniform(1, 5, 100)
    }

    df = pd.DataFrame(data)

    # Temel istatistikler
    print("\\nVeri Seti Özeti:")
    print(df.describe())

    # Görselleştirme
    plt.figure(figsize=(12, 8))

    plt.subplot(2, 2, 1)
    df['satış'].hist(bins=20)
    plt.title('Satış Dağılımı')

    plt.subplot(2, 2, 2)
    df.groupby('kategori')['satış'].mean().plot(kind='bar')
    plt.title('Kategoriye Göre Ortalama Satış')

    plt.subplot(2, 2, 3)
    plt.scatter(df['müşteri_puanı'], df['satış'])
    plt.xlabel('Müşteri Puanı')
    plt.ylabel('Satış')
    plt.title('Müşteri Puanı vs Satış')

    plt.subplot(2, 2, 4)
    df.set_index('tarih')['satış'].plot()
    plt.title('Zaman Serisi Satış')

    plt.tight_layout()
    plt.savefig('analiz_sonuçları.png', dpi=300, bbox_inches='tight')
    plt.show()

    print("\\nAnaliz tamamlandı! Grafik 'analiz_sonuçları.png' olarak kaydedildi.")

if __name__ == "__main__":
    main()
'''
                else:
                    content = f'''#!/usr/bin/env python3
"""
{filename} - AI Geliştirici Asistanı tarafından oluşturuldu
"""

def main():
    """Ana fonksiyon"""
    print("Merhaba, {filename}!")

if __name__ == "__main__":
    main()
'''

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)

            os.chmod(filename, 0o755)  # Çalıştırılabilir yapılandır
            print(f"✅ {filename} başarıyla oluşturuldu!")
            return True

        except Exception as e:
            print(f"❌ Dosya oluşturma hatası: {e}")
            return False

    def install_data_science_libraries(self) -> bool:
        """Veri analizi kütüphanelerini yükle"""
        print("📦 Veri analizi kütüphaneleri yükleniyor...")

        # requirements.txt oluştur
        requirements_content = "\n".join(self.data_science_libraries)
        with open('requirements.txt', 'w') as f:
            f.write(requirements_content)

        print("✅ requirements.txt oluşturuldu!")

        # Kütüphaneleri yükle
        success, stdout, stderr = self.execute_command("pip install -r requirements.txt")

        if success:
            print("✅ Tüm kütüphaneler başarıyla yüklendi!")
            return True
        else:
            print(f"❌ Kütüphane yükleme hatası: {stderr}")
            return False

    def list_directory(self, path: str = ".") -> None:
        """Dizin içeriğini listele"""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                print(f"❌ Dizin bulunamadı: {path}")
                return

            print(f"📁 {path_obj.absolute()} içeriği:")
            print("-" * 50)

            items = list(path_obj.iterdir())
            items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))

            for item in items:
                if item.is_dir():
                    print(f"📁 {item.name}/")
                else:
                    size = item.stat().st_size
                    print(f"📄 {item.name} ({size} bytes)")

        except Exception as e:
            print(f"❌ Dizin listeleme hatası: {e}")

    def init_git_and_push(self) -> bool:
        """Git başlat ve GitHub'a yükle"""
        print("🔄 Git repository başlatılıyor...")

        # Git repository'i başlat
        success, _, _ = self.execute_command("git init")
        if not success:
            print("❌ Git repository başlatılamadı!")
            return False

        # .gitignore oluştur
        gitignore_content = """__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.venv/
.DS_Store
.idea/
.vscode/
*.log
*.sqlite3
.ai_dev_config.json
"""
        with open('.gitignore', 'w') as f:
            f.write(gitignore_content)

        # GitHub bilgilerini al
        if 'github_url' not in self.project_config:
            github_url = input("🔗 GitHub repository URL'nizi girin: ").strip()
            if not github_url:
                print("❌ GitHub URL gerekli!")
                return False
            self.project_config['github_url'] = github_url
            self.save_project_config()

        commit_message = input("💬 İlk commit mesajınızı girin: ").strip()
        if not commit_message:
            commit_message = "İlk commit - AI Geliştirici Asistanı"

        # Git komutlarını çalıştır
        commands = [
            "git add .",
            f'git commit -m "{commit_message}"',
            f"git remote add origin {self.project_config['github_url']}",
            "git branch -M main",
            "git push -u origin main"
        ]

        for cmd in commands:
            print(f"🔄 Çalıştırılıyor: {cmd}")
            success, stdout, stderr = self.execute_command(cmd)
            if not success and "already exists" not in stderr:
                print(f"❌ Komut hatası: {stderr}")
                if "remote add origin" in cmd:
                    # Remote zaten varsa güncelle
                    self.execute_command("git remote set-url origin " + self.project_config['github_url'])
                    continue
                return False

        print("✅ Proje başarıyla GitHub'a yüklendi!")
        return True

    def push_changes(self) -> bool:
        """Değişiklikleri GitHub'a yükle"""
        if 'github_url' not in self.project_config:
            print("❌ GitHub URL bulunamadı! Önce projeyi GitHub'a yükleyin.")
            return False

        commit_message = input("💬 Commit mesajınızı girin: ").strip()
        if not commit_message:
            commit_message = "Güncellemeler"

        commands = [
            "git add .",
            f'git commit -m "{commit_message}"',
            "git push origin main"
        ]

        for cmd in commands:
            print(f"🔄 Çalıştırılıyor: {cmd}")
            success, stdout, stderr = self.execute_command(cmd)
            if not success:
                print(f"❌ Komut hatası: {stderr}")
                return False

        print("✅ Değişiklikler başarıyla GitHub'a yüklendi!")
        return True

    def create_file(self, filename: str, content: str = "") -> bool:
        """Genel dosya oluştur"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {filename} başarıyla oluşturuldu!")
            return True
        except Exception as e:
            print(f"❌ Dosya oluşturma hatası: {e}")
            return False

    def process_gemma_command(self, user_input: str) -> None:
        """Kullanıcı komutunu işle (Gemma 3 entegrasyonu için hazır)"""
        user_input = user_input.lower().strip()

        # Komut analizi
        if "dosya dizini göster" in user_input or "ls" in user_input or "dir" in user_input:
            self.list_directory()

        elif "python dosyası oluştur" in user_input or "app.py oluştur" in user_input:
            if "app.py" in user_input or "app" in user_input:
                self.create_python_file("app.py")
            else:
                filename = input("📝 Oluşturulacak Python dosyasının adını girin: ")
                if filename:
                    self.create_python_file(filename)

        elif "kütüphane" in user_input and ("yükle" in user_input or "install" in user_input):
            self.install_data_science_libraries()

        elif "github" in user_input and ("yükle" in user_input or "push" in user_input):
            if "ilk" in user_input or "başlat" in user_input:
                self.init_git_and_push()
            else:
                self.push_changes()

        elif "son çalışmalarımı" in user_input and "github" in user_input:
            self.push_changes()

        elif "dosya oluştur" in user_input:
            filename = input("📝 Oluşturulacak dosyanın adını girin: ")
            if filename:
                content = input("📄 Dosya içeriği (boş bırakabilirsiniz): ")
                self.create_file(filename, content)

        elif user_input in ["exit", "quit", "çıkış", "q"]:
            print("👋 Görüşürüz!")
            sys.exit(0)

        elif user_input in ["help", "yardım", "?"]:
            self.show_help()

        else:
            print("🤔 Komut anlaşılamadı. Yardım için 'help' yazın.")

    def show_help(self):
        """Yardım menüsünü göster"""
        help_text = """
🤖 AI Geliştirici Asistanı - Komut Listesi
=========================================

📁 Dosya İşlemleri:
  • dosya dizini göster        - Mevcut dizindeki dosyaları listele
  • python dosyası oluştur      - Python dosyası oluştur
  • app.py oluştur             - Veri analizi app.py dosyası oluştur
  • dosya oluştur              - Genel dosya oluştur

📦 Kütüphane İşlemleri:
  • kütüphane yükle            - Veri analizi kütüphanelerini yükle

🔗 GitHub İşlemleri:
  • github'a yükle             - İlk defa GitHub'a yükle
  • son çalışmalarımı github'a at - Değişiklikleri GitHub'a gönder

🔧 Diğer:
  • help / yardım              - Bu yardım menüsünü göster
  • exit / çıkış               - Uygulamadan çık

💡 İpucu: Komutları doğal dilde yazabilirsiniz!
"""
        print(help_text)

    def run(self):
        """Ana çalışma döngüsü"""
        print("🤖 AI Geliştirici Asistanı Başlatıldı!")
        print("💡 Komutlarınızı doğal dilde yazabilirsiniz. Yardım için 'help' yazın.")
        print("-" * 60)

        while True:
            try:
                user_input = input("\n🔤 Komutunuzu girin: ").strip()
                if user_input:
                    self.process_gemma_command(user_input)

            except KeyboardInterrupt:
                print("\n\n👋 Görüşürüz!")
                break
            except Exception as e:
                print(f"❌ Hata: {e}")


def main():
    """Ana fonksiyon"""
    assistant = AIDevAssistant()
    assistant.run()


if __name__ == "__main__":
    main()