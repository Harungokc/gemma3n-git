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
        context_parts = []
        try:
            context_parts.append(f"Mevcut Dizin: {os.getcwd()}")
            if os.path.isdir('.git'):
                context_parts.append("Durum: Bu bir Git deposu.")
                branch_result = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True, timeout=5)
                if branch_result.returncode == 0 and branch_result.stdout.strip():
                    context_parts.append(f"Aktif Dal: {branch_result.stdout.strip()}")
                status_result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, timeout=5)
                if status_result.returncode == 0:
                    context_parts.append("Git Durumu: Temiz (kaydedilecek değişiklik yok)." if not status_result.stdout.strip() else "Git Durumu: Kaydedilmemiş değişiklikler var.")
                remote_result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True, timeout=5)
                if remote_result.returncode == 0 and 'origin' in remote_result.stdout:
                    context_parts.append("Uzak Depo: 'origin' ayarlanmış.")
                else:
                    context_parts.append("Uzak Depo: 'origin' ayarlanmamış.")
            else:
                context_parts.append("Durum: Bu bir Git deposu değil.")
            return "\n".join(context_parts)
        except Exception as e:
            return f"Mevcut Dizin: {os.getcwd()}\nBağlam alınırken hata: {e}"

    def get_command_from_gemma(self, user_prompt):
        context = self.gather_context()
        prompt = f"""
Sen duruma göre hareket eden, akıllı bir terminal komut asistanısın.
Sana verilen BAĞLAM BİLGİSİ'ni analiz et ve kullanıcının talebini bu bağlama en uygun şekilde yerine getirecek komutları üret.
Örneğin, eğer bağlamda "Bu bir Git deposu" deniyorsa, `git init` komutunu tekrar üretme.
Eğer "Uzak Depo: 'origin' ayarlanmış" deniyorsa, `git remote add` komutunu tekrar üretme.
---
BAĞLAM BİLGİSİ:
{context}
---
KURALLAR:
1. Sadece ve sadece çalıştırılabilir komutlar üret.
2. Açıklama yapma.
3. Birden fazla komut gerekirse her birini yeni satıra yaz.
4. Gerekli bilgiler eksikse (proje adı, commit mesajı vb.) <BÜYÜK_HARFLE_AÇIKLAMA> şeklinde bir yer tutucu kullan.
5. YENİ KURAL: `git push` komutlarında, kullanıcı farklı bir dal belirtmediği sürece her zaman `main` dalını hedefle. Bunun için <BRANCH_ADI> gibi bir yer tutucu sorma.
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
            result = response.json(); raw_command_text = result.get('response', '').strip()
            clean_text = raw_command_text.replace('Komut:', '').replace('```', '').replace('`', '').strip()
            commands = [cmd.strip() for cmd in clean_text.split('\n') if cmd.strip()]
            if not commands: return None
            return commands[0] if len(commands) == 1 else commands
        except requests.exceptions.RequestException as e:
            print(f"❌ Ollama ile bağlantı hatası: {e}"); return None
        except Exception as e: print(f"❌ Beklenmeyen hata: {e}"); return None

    def is_safe_command(self, command):
        if not command: return False
        dangerous_commands = ['rm -rf', 'rm -fr', 'format', 'fdisk', 'mkfs', 'dd if=', 'shutdown', 'reboot', 'halt', '> /etc/', 'mv /* ', 'cp /* ']
        command_lower = command.lower(); command_parts_for_danger_check = command_lower.split()
        for part in command_parts_for_danger_check:
            if part in dangerous_commands: print(f"🔍 Tehlikeli parça bulundu: '{part}'"); return False
        safe_commands = ['touch', 'mkdir', 'ls', 'pwd', 'cd', 'cat', 'echo', 'cp', 'mv', 'find', 'grep', 'head', 'tail', 'wc', 'sort', 'date', 'whoami', 'which', 'file', 'git']
        command_parts = command.strip().split()
        if command_parts:
            first_command = command_parts[0].split('/')[-1]
            return first_command in safe_commands
        return False

    def execute_command(self, command):
        if not self.is_safe_command(command):
            print(f"⚠️  Güvenlik nedeniyle bu komut çalıştırılamaz: {command}"); return False
        try:
            print(f"🚀 Çalıştırılıyor: {command}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("✅ Komut başarıyla çalıştırıldı!");
                if result.stdout: print(f"📤 Çıktı:\n{result.stdout.strip()}")
                if result.stderr: print(f"ℹ️ Bilgi/Uyarı:\n{result.stderr.strip()}")
            else: print(f"❌ Komut hatalı: {result.stderr.strip()}")
            return result.returncode == 0
        except subprocess.TimeoutExpired: print("⏱️  Komut zaman aşımına uğradı!"); return False
        except Exception as e: print(f"❌ Komut çalıştırılırken hata: {e}"); return False

    def execute_command_sequence(self, commands):
        processed_commands = []
        commands_to_process = list(commands)
        for i, command in enumerate(commands_to_process):
            if 'git commit -m' in command:
                print("ℹ️ Commit komutu algılandı. Mesaj size sorulacak.")
                command = 'git commit -m "<COMMIT_MESAJI>"'
                commands_to_process[i] = command
            if "<" in command and ">" in command:
                placeholder = command[command.find("<"):command.find(">") + 1]
                try: user_value = input(f"ℹ️ Lütfen '{placeholder}' için bir değer girin: ")
                except EOFError: print("\n❌ Giriş iptal edildi."); user_value = ""
                final_command = command.replace(placeholder, user_value)
                processed_commands.append(final_command)
            else: processed_commands.append(command)
        print("\n--- Çalıştırılacak Komut Dizisi ---")
        for i, cmd in enumerate(processed_commands, 1): print(f"{i}. {cmd}")
        print("---------------------------------")
        try: confirm = input("✅ Bu komut dizisini çalıştırmak istiyor musunuz? (e/h): ").strip().lower()
        except EOFError: confirm = 'h'
        if confirm not in ['e', 'evet', 'yes', 'y']: print("❌ Komut dizisi iptal edildi."); return
        original_directory = os.getcwd()
        for cmd in processed_commands:
            if cmd.strip().startswith('cd '):
                try:
                    target_dir = cmd.strip()[3:]
                    os.chdir(target_dir); print(f"✅ Çalışma dizini değiştirildi: {os.getcwd()}")
                    continue
                except FileNotFoundError: print(f"❌ Dizin bulunamadı: {target_dir}. İşlem durduruldu."); break
                except Exception as e: print(f"❌ Dizin değiştirilirken hata oluştu: {e}. İşlem durduruldu."); break
            success = self.execute_command(cmd)
            if not success:
                print(f"❌ Komut '{cmd}' başarısız olduğu için dizi durduruldu.")
                os.chdir(original_directory); break

    def run(self):
        print("🤖 Akıllı Proje Asistanı v9 (Stabil Push) başlatıldı!")
        print("💡 Örnek: 'yeni bir proje başlat ve githuba gönder'")
        print("📁 Mevcut dizin:", os.getcwd()); print("-" * 50)
        while True:
            try:
                user_input = input("\n🎯 Komut girin (çıkış: 'exit'): ").strip()
                if not user_input: continue
                if user_input.lower() in ['exit', 'quit', 'çıkış']: print("👋 Görüşürüz!"); break
                command_or_list = self.get_command_from_gemma(user_input)
                if not command_or_list: print("❌ Komut alınamadı, tekrar deneyin."); continue
                if isinstance(command_or_list, list): self.execute_command_sequence(command_or_list)
                else:
                    command = command_or_list
                    print(f"🔍 Önerilen komut: {command}")
                    confirm = input("✅ Bu komutu çalıştırmak istiyor musunuz? (e/h): ").strip().lower()
                    if confirm in ['e', 'evet', 'yes', 'y']: self.execute_command(command)
                    else: print("❌ Komut iptal edildi.")
            except KeyboardInterrupt: print("\n👋 Program sonlandırıldı!"); break
            except Exception as e: print(f"❌ Ana döngüde beklenmeyen hata: {e}")

if __name__ == "__main__":
    assistant = TerminalAssistant()
    assistant.run()