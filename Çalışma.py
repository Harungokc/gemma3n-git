import requests
import subprocess
import json
import os
import sys


class TerminalAssistant:
    def __init__(self):
        self.ollama_model = "gemma3n"
        self.ollama_url = "http://localhost:11434/api/generate"
        # DEĞİŞTİRİLDİ: Veri bilimi için standart kütüphaneler listesi eklendi.
        self.data_science_libraries = "pandas numpy matplotlib seaborn scikit-learn jupyterlab"

    def gather_context(self) -> str:
        """Projenin mevcut durumu hakkında detaylı bağlam toplar."""
        context_parts = []
        current_dir = os.getcwd()
        context_parts.append(f"Mevcut Dizin: {current_dir}")
        context_parts.append(
            f"Dizin İçeriği: {', '.join(os.listdir(current_dir)[:10])}")  # İlk 10 dosyayı/klasörü göster

        # Sanal ortam kontrolü eklendi
        if os.path.isdir('.venv'):
            context_parts.append("Sanal Ortam: '.venv' adında bir sanal ortam mevcut.")
        else:
            context_parts.append("Sanal Ortam: Mevcut dizinde sanal ortam bulunmuyor.")

        if not os.path.isdir('.git'):
            context_parts.append("Durum: Bu bir Git deposu değil.")
            return "\n".join(context_parts)

        # ... (Geri kalan Git kontrolleri aynı kalabilir)
        context_parts.append("Durum: Bu bir Git deposu.")
        branch_result = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True, timeout=5)
        if branch_result.returncode == 0 and branch_result.stdout.strip():
            context_parts.append(f"Aktif Dal: {branch_result.stdout.strip()}")
        status_result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, timeout=5)
        if status_result.returncode == 0:
            context_parts.append(
                "Git Durumu: Temiz (kaydedilecek değişiklik yok)." if not status_result.stdout.strip() else "Git Durumu: Kaydedilmemiş değişiklikler var.")
        remote_result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True, timeout=5)
        if remote_result.returncode == 0 and 'origin' in remote_result.stdout:
            context_parts.append("Uzak Depo: 'origin' ayarlanmış.")
        else:
            context_parts.append("Uzak Depo: 'origin' ayarlanmamış.")
        return "\n".join(context_parts)

    def get_command_from_gemma(self, user_prompt):
        context = self.gather_context()
        # DEĞİŞTİRİLDİ: Prompt, veri bilimi görevlerini anlayacak şekilde güncellendi.
        prompt = f"""
Sen bir veri bilimcinin proje kurulum ve yönetim süreçlerini otomatikleştiren, akıllı bir terminal asistanısın.
BAĞLAM BİLGİSİ'ni ve KULLANICI TALEBİ'ni analiz ederek en uygun komutları üret.

---
BAĞLAM BİLGİSİ:
{context}
---
YETENEKLERİN ve KURALLARIN:
1.  Sadece çalıştırılabilir terminal komutları üret. Asla açıklama yapma.
2.  **Veri Bilimi Projesi Kurulumu:** Eğer kullanıcı yeni bir veri bilimi projesi başlatmak isterse, şu adımları uygula:
    a. `python3 -m venv .venv` komutuyla bir sanal ortam oluştur (eğer bağlamda zaten yoksa).
    b. Proje yapılandırması için `data`, `notebooks`, `scripts` adında klasörler oluştur.
    c. Python dosyaları için standart bir `.gitignore` dosyası oluştur (`touch .gitignore` ve sonra `echo '.venv/\n*.pyc\n__pycache__/' > .gitignore`).
3.  **Kütüphane Yükleme:** Eğer kullanıcı "veri bilimi/analizi kütüphanelerini yükle" gibi bir talepte bulunursa, şu komutu üret: `pip install {self.data_science_libraries}`. Bu komutu sanal ortam aktifken çalıştırmak kullanıcının sorumluluğundadır.
4.  **Dosya/Klasör Oluşturma:** Kullanıcı "bana 'analiz.ipynb' adında bir dosya oluştur" derse, projenin yapısına uygun olarak (`touch notebooks/analiz.ipynb` gibi) komut üret.
5.  **Git İşlemleri:**
    a. Bağlamda "Git Durumu: Temiz" yazıyorsa `git add` veya `git commit` üretme.
    b. `git push` için bağlamdaki "Aktif Dal" adını kullan.
6.  Eksik bilgi varsa <BÜYÜK_HARFLE_AÇIKLAMA> şeklinde yer tutucu kullan.
---
KULLANICI TALEBİ: {user_prompt}
---
SADECE KOMUTLAR:
"""
        payload = {"model": self.ollama_model, "prompt": prompt, "stream": False}
        try:
            print("🧠 Veri Bilimci Asistanı durumu analiz ediyor ve komut üretiyor...")
            response = requests.post(self.ollama_url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json();
            raw_command_text = result.get('response', '').strip()
            clean_text = raw_command_text.replace('```', '').replace('`', '').strip()
            commands = [cmd.strip() for cmd in clean_text.split('\n') if cmd.strip()]
            if not commands: return None
            return commands[0] if len(commands) == 1 else commands
        except requests.exceptions.RequestException as e:
            print(f"❌ Ollama ile bağlantı hatası: {e}");
            return None
        except Exception as e:
            print(f"❌ Beklenmeyen hata: {e}"); return None

    def is_safe_command(self, command):
        if not command: return False
        dangerous_patterns = ['rm -rf', 'rm -fr', '> /etc/', 'mv /*']
        for pattern in dangerous_patterns:
            if pattern in command:
                return False

        # DEĞİŞTİRİLDİ: 'pip' ve 'python3' güvenli komutlar listesine eklendi.
        safe_commands = ['touch', 'mkdir', 'ls', 'pwd', 'cd', 'cat', 'echo', 'cp', 'mv', 'git', 'pip', 'python3',
                         'source']
        command_start = command.strip().split()[0]
        if '/' in command_start:  # Eğer /venv/bin/pip gibi bir komutsa
            command_start = command_start.split('/')[-1]
        return command_start in safe_commands

    def execute_command(self, command):
        if not self.is_safe_command(command):
            print(f"⚠️  Güvenlik nedeniyle bu komut çalıştırılamaz: {command}");
            return False

        # Sanal ortam aktivasyonu gibi özel durumları ele al
        if command.strip().startswith('source '):
            print(
                f"ℹ️ Sanal ortamı aktive etmek için lütfen bu komutu manuel olarak terminalinizde çalıştırın: {command}")
            print("ℹ️ Not: Script'ler, kendi çalıştıkları shell'in dışındaki ortamı değiştiremezler.")
            return True  # Komutu başarılı sayarak devam et

        try:
            print(f"🚀 Çalıştırılıyor: {command}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True,
                                    timeout=300)  # Timeout artırıldı

            # Pip'in "zaten yüklü" mesajını başarı olarak kabul et
            if "Requirement already satisfied" in result.stdout or "Gereksinim zaten karşılandı" in result.stdout:
                print("✅ Kütüphaneler zaten yüklü.")
                return True

            if result.returncode == 0:
                print("✅ Komut başarıyla çalıştırıldı!");
                if result.stdout: print(f"📤 Çıktı:\n{result.stdout.strip()}")
                if result.stderr: print(f"ℹ️ Bilgi/Uyarı:\n{result.stderr.strip()}")
            else:
                print(f"❌ Komut hatalı: {result.stderr.strip() or result.stdout.strip()}")
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("⏱️  Komut (kütüphane yüklemesi olabilir) zaman aşımına uğradı!"); return False
        except Exception as e:
            print(f"❌ Komut çalıştırılırken hata: {e}"); return False

    # execute_command_sequence ve run fonksiyonları büyük ölçüde aynı kalabilir.
    # Onları buraya yeniden eklemeye gerek yok, mevcut halleriyle çalışacaklardır.

    def execute_command_sequence(self, commands):
        # Bu fonksiyon önceki versiyondaki gibi kalabilir.
        processed_commands = []
        for command in commands:
            if "<" in command and ">" in command:
                placeholder = command[command.find("<"):command.find(">") + 1]
                try:
                    user_value = input(f"ℹ️ Lütfen '{placeholder}' için bir değer girin: ")
                except EOFError:
                    print("\n❌ Giriş iptal edildi."); return
                final_command = command.replace(placeholder, user_value)
                processed_commands.append(final_command)
            else:
                processed_commands.append(command)
        print("\n--- Çalıştırılacak Komut Dizisi ---")
        for i, cmd in enumerate(processed_commands, 1): print(f"{i}. {cmd}")
        print("---------------------------------")
        try:
            confirm = input("✅ Bu komut dizisini çalıştırmak istiyor musunuz? (e/h): ").strip().lower()
        except EOFError:
            confirm = 'h'
        if confirm not in ['e', 'evet', 'yes', 'y']: print("❌ Komut dizisi iptal edildi."); return
        original_directory = os.getcwd()
        for cmd in processed_commands:
            if cmd.strip().startswith('cd '):
                try:
                    target_dir = cmd.strip()[3:];
                    os.chdir(target_dir);
                    print(f"✅ Çalışma dizini değiştirildi: {os.getcwd()}");
                    continue
                except Exception as e:
                    print(f"❌ Dizin değiştirilirken hata oluştu: {e}. İşlem durduruldu."); break
            if not self.execute_command(cmd):
                print(f"❌ Komut '{cmd}' başarısız olduğu için dizi durduruldu.");
                os.chdir(original_directory);
                break

    def run(self):
        # Bu fonksiyon önceki versiyondaki gibi kalabilir.
        print("🤖 Akıllı Veri Bilimci Asistanı v11 başlatıldı!")
        print("💡 Örnek: 'yeni bir veri analizi projesi başlat' veya 'gerekli kütüphaneleri yükle'")
        print("📁 Mevcut dizin:", os.getcwd());
        print("-" * 50)
        while True:
            try:
                user_input = input("\n🎯 Ne yapmak istersin? (çıkış: 'exit'): ").strip()
                if not user_input: continue
                if user_input.lower() in ['exit', 'quit', 'çıkış']: print("👋 Görüşürüz!"); break
                command_or_list = self.get_command_from_gemma(user_input)
                if not command_or_list: print("✅ Yapılacak bir işlem bulunamadı veya her şey güncel."); continue
                if isinstance(command_or_list, list):
                    self.execute_command_sequence(command_or_list)
                else:
                    command = command_or_list;
                    print(f"🔍 Önerilen komut: {command}")
                    confirm = input("✅ Bu komutu çalıştırmak istiyor musunuz? (e/h): ").strip().lower()
                    if confirm in ['e', 'evet', 'yes', 'y']:
                        self.execute_command(command)
                    else:
                        print("❌ Komut iptal edildi.")
            except KeyboardInterrupt:
                print("\n👋 Program sonlandırıldı!"); break
            except Exception as e:
                print(f"❌ Ana döngüde beklenmeyen hata: {e}")


if __name__ == "__main__":
    # Önemli Not: En iyi sonuç için bu script'i projenizin ana klasöründe çalıştırın.
    assistant = TerminalAssistant()
    assistant.run()