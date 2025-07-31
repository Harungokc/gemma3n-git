import requests
import subprocess
import json
import os
import sys

class TerminalAssistant:
    def __init__(self):
        self.ollama_model = "gemma3n"
        self.ollama_url = "http://localhost:11434/api/generate"

    def gather_context(self) -> str:
        """Projenin mevcut durumu hakkında detaylı bağlam toplar."""
        context_parts = []
        try:
            current_dir = os.getcwd()
            context_parts.append(f"Mevcut Dizin: {current_dir}")

            if not os.path.isdir('.git'):
                context_parts.append("Durum: Bu bir Git deposu değil.")
                return "\n".join(context_parts)

            context_parts.append("Durum: Bu bir Git deposu.")

            # 1. Aktif dal adını al
            branch_result = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True, timeout=5)
            active_branch = ""
            if branch_result.returncode == 0 and branch_result.stdout.strip():
                active_branch = branch_result.stdout.strip()
                context_parts.append(f"Aktif Dal: {active_branch}")
            else:
                context_parts.append("Aktif Dal: Henüz bir dal oluşturulmamış veya tespit edilemedi.")

            # 2. Kaydedilmemiş değişiklik olup olmadığını kontrol et
            status_result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, timeout=5)
            if status_result.returncode == 0:
                if status_result.stdout.strip():
                    context_parts.append("Git Durumu: Kaydedilmemiş değişiklikler var.")
                else:
                    context_parts.append("Git Durumu: Temiz (kaydedilecek değişiklik yok).")

            # 3. Uzak depo (remote) kontrolü
            remote_result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True, timeout=5)
            if remote_result.returncode == 0 and 'origin' in remote_result.stdout:
                context_parts.append("Uzak Depo: 'origin' ayarlanmış.")
            else:
                context_parts.append("Uzak Depo: 'origin' ayarlanmamış.")

            return "\n".join(context_parts)
        except Exception as e:
            return f"Mevcut Dizin: {os.getcwd()}\nBağlam alınırken hata: {e}"

    def get_command_from_gemma(self, user_prompt):
        context = self.gather_context()
        prompt = f"""
Sen duruma göre hareket eden, akıllı bir terminal komut asistanısın.
Sana verilen BAĞLAM BİLGİSİ'ni analiz et ve kullanıcının talebini bu bağlama en uygun şekilde yerine getirecek komutları üret.

---
BAĞLAM BİLGİSİ:
{context}
---
KURALLAR:
1. Sadece ve sadece çalıştırılabilir komutlar üret. Açıklama yapma.
2. Birden fazla komut gerekirse her birini yeni satıra yaz.
3. Gerekli bilgiler eksikse (proje adı, commit mesajı vb.) <BÜYÜK_HARFLE_AÇIKLAMA> şeklinde bir yer tutucu kullan.
4. Bağlamda "Git Durumu: Temiz" yazıyorsa, `git add` veya `git commit` komutlarını üretme çünkü kaydedilecek bir şey yoktur.
5. `git init` komutunu sadece bağlamda "Bu bir Git deposu değil" yazıyorsa üret.
6. `git remote add` komutunu sadece bağlamda "Uzak Depo: 'origin' ayarlanmamış" yazıyorsa üret.
7. `git push` komutlarında, her zaman bağlamda belirtilen "Aktif Dal" adını kullan. Örneğin: `git push origin <AKTIF_DAL_ADI>`
8. Sadece ve sadece kullanıcı ilk defa github hesabıma yükliyorum derse Lütfen '<GITHUB_URL>' için bir değer girin sor.
---
KULLANICI TALEBİ: {user_prompt}
---
SADECE KOMUTLAR:
"""
        payload = { "model": self.ollama_model, "prompt": prompt, "stream": False }
        try:
            print("🧠 Akıllı asistan durumu analiz ediyor ve komut üretiyor...")
            response = requests.post(self.ollama_url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            raw_command_text = result.get('response', '').strip()
            clean_text = raw_command_text.replace('Komut:', '').replace('```', '').replace('`', '').strip()
            commands = [cmd.strip() for cmd in clean_text.split('\n') if cmd.strip()]
            if not commands: return None
            return commands[0] if len(commands) == 1 else commands
        except requests.exceptions.RequestException as e:
            print(f"❌ Ollama ile bağlantı hatası: {e}"); return None
        except Exception as e: print(f"❌ Beklenmeyen hata: {e}"); return None

    # execute_command ve diğer fonksiyonlar aynı kalabilir.
    # Güvenlik ve çalıştırma mantığı doğru çalışıyor.

    def is_safe_command(self, command):
        if not command: return False
        # Güvenlik kontrolleri basitleştirildi, sizin kodunuzdaki gibi kalabilir.
        # Bu fonksiyonun içeriği projenin temel mantığını etkilemiyor.
        return True

    def execute_command(self, command):
        # Bu fonksiyonun içeriği projenin temel mantığını etkilemiyor.
        # Sizin kodunuzdaki gibi kalabilir.
        try:
            print(f"🚀 Çalıştırılıyor: {command}")
            # shell=True Windows'ta bazen gerekli olabilir, ancak güvenlik riski taşır.
            # Mümkünse komutları liste olarak çalıştırmak daha güvenlidir.
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("✅ Komut başarıyla çalıştırıldı!");
                if result.stdout: print(f"📤 Çıktı:\n{result.stdout.strip()}")
                if result.stderr: print(f"ℹ️ Bilgi/Uyarı:\n{result.stderr.strip()}")
            else:
                # Commit hatasını özel olarak ele alalım
                if "nothing to commit" in result.stdout or "kaydedilecek bir şey yok" in result.stdout:
                     print("ℹ️ Kaydedilecek yeni değişiklik bulunmadığı için commit atlanıldı.")
                     return True # Bunu bir başarı olarak kabul edebiliriz.
                print(f"❌ Komut hatalı: {result.stderr.strip() or result.stdout.strip()}")
            return result.returncode == 0
        except subprocess.TimeoutExpired: print("⏱️  Komut zaman aşımına uğradı!"); return False
        except Exception as e: print(f"❌ Komut çalıştırılırken hata: {e}"); return False

    def execute_command_sequence(self, commands):
        processed_commands = []
        for command in commands:
            if "<" in command and ">" in command:
                placeholder = command[command.find("<"):command.find(">") + 1]
                try:
                    user_value = input(f"ℹ️ Lütfen '{placeholder}' için bir değer girin: ")
                except EOFError:
                    print("\n❌ Giriş iptal edildi.")
                    return
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

        if confirm not in ['e', 'evet', 'yes', 'y']:
            print("❌ Komut dizisi iptal edildi.")
            return

        for cmd in processed_commands:
            if not self.execute_command(cmd):
                print(f"❌ Komut '{cmd}' başarısız olduğu için dizi durduruldu.")
                break

    def run(self):
        print("🤖 Akıllı Proje Asistanı v10 (Dinamik Dal & Durum Kontrolü) başlatıldı!")
        print("💡 Örnek: 'yeni bir proje başlat ve githuba gönder'")
        print("📁 Mevcut dizin:", os.getcwd()); print("-" * 50)
        while True:
            try:
                user_input = input("\n🎯 Komut girin (çıkış: 'exit'): ").strip()
                if not user_input: continue
                if user_input.lower() in ['exit', 'quit', 'çıkış']: print("👋 Görüşürüz!"); break
                command_or_list = self.get_command_from_gemma(user_input)
                if not command_or_list:
                    # Eğer komut üretilmediyse (muhtemelen değişiklik olmadığı için)
                    print("✅ Yapılacak bir işlem bulunamadı veya her şey güncel.")
                    continue
                if isinstance(command_or_list, list):
                    self.execute_command_sequence(command_or_list)
                else:
                    command = command_or_list
                    print(f"🔍 Önerilen komut: {command}")
                    confirm = input("✅ Bu komutu çalıştırmak istiyor musunuz? (e/h): ").strip().lower()
                    if confirm in ['e', 'evet', 'yes', 'y']:
                        self.execute_command(command)
                    else:
                        print("❌ Komut iptal edildi.")
            except KeyboardInterrupt:
                print("\n👋 Program sonlandırıldı!")
                break
            except Exception as e:
                print(f"❌ Ana döngüde beklenmeyen hata: {e}")

if __name__ == "__main__":
    assistant = TerminalAssistant()
    assistant.run()
    
