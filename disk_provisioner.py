import tkinter as tk
from tkinter import messagebox
import threading
import time
import subprocess
import wmi
import pythoncom
import os

class DiskProvisionerApp:
    def __init__(self, root):
        # 1. UI 초기화 설정
        self.root = root
        self.root.title("USB 디스크 초기화 자동화 시스템")
        self.root.geometry("800x400")
        self.root.configure(padx=20, pady=20)
        
        self.label = tk.Label(
            root, 
            text="디스크 삽입 대기 중...", 
            font=("Malgun Gothic", 28, "bold"),
            justify="center"
            
        )
        self.label.pack(expand=True)

        # 2. 상태 통제 변수
        self.current_disk = None
        self.is_waiting_for_user = False
        self.known_disks = set()

        # 3. 키보드 이벤트 바인딩
        self.root.bind('<Return>', self.execute_format_action)
        self.root.bind('<Escape>', self.cancel_and_reset_action)

        # 4. WMI 모니터링 백그라운드 스레드 시작
        self.monitor_thread = threading.Thread(target=self.monitor_wmi_events, daemon=True)
        self.monitor_thread.start()

    def monitor_wmi_events(self):
        # 스레드 내 COM 객체 초기화 (pywin32 필수)
        pythoncom.CoInitialize()
        wmi_conn = wmi.WMI(namespace="root\\wmi")
        
        # 프로그램 시작 시점에 연결되어 있는 기존 디스크 목록을 화이트리스트(무시 대상)로 등록
        try:
            for hds in wmi_conn.HDSentinel():
                self.known_disks.add(hds.ID)
        except Exception:
            pass

        while True:
            time.sleep(1) # 1초 주기로 폴링하여 부하 최소화
            
            # 사용자 판단 대기 중에는 추가 스캔 중지
            if self.is_waiting_for_user:
                continue

            try:
                for hds in wmi_conn.HDSentinel():
                    disk_id = getattr(hds, "ID", "")
                    
                    # 새로운 디스크가 감지된 경우
                    if disk_id and disk_id not in self.known_disks:
                        self.known_disks.add(disk_id)
                        interface_type = getattr(hds, "Interface", "").upper()

                        # [안전 통제]: USB 인터페이스로 연결된 기기만 허용
                        if "USB" in interface_type:
                            health = getattr(hds, "Health", "Unknown")
                            model = getattr(hds, "ModelID", "Unknown")
                            
                            # diskpart 선택을 위한 물리적 인덱스 추출 (예: "Drive 2" -> "2")
                            physical_index = disk_id.replace("Drive ", "").strip()
                            
                            self.current_disk = {
                                "ID": disk_id,
                                "Model": model,
                                "Health": health,
                                "PhysicalIndex": physical_index
                            }
                            
                            # UI 업데이트는 메인 스레드에서 실행되도록 위임
                            self.root.after(0, self.update_ui_for_decision)
            except Exception:
                pass # HD Sentinel 미실행 등 WMI 예외 발생 시 무시하고 다음 루프 대기

    def update_ui_for_decision(self):
        self.is_waiting_for_user = True
        display_text = (
            f"인식 모델: {self.current_disk['Model']}\n"
            f"건강 상태(Health): {self.current_disk['Health']}%\n\n"
            f"[Enter] 초기화 진행   |   [ESC] 불량 처리"
        )
        self.label.config(text=display_text, fg="#0052cc")

    def execute_format_action(self, event=None):
        if not self.is_waiting_for_user or not self.current_disk:
            return

        # 중복 입력 방지 및 UI 업데이트
        self.is_waiting_for_user = False
        self.label.config(text="초기화 진행 중... 절대 디스크를 분리하지 마세요.", fg="#d04437")
        self.root.update()

        disk_idx = self.current_disk['PhysicalIndex']
        script_path = os.path.join(os.environ["TEMP"], "diskpart_script.txt")
        
        # diskpart 스크립트 작성 (clean -> 파티션 생성 -> 빠른 포맷 -> 드라이브 문자 할당)
        script_content = f"select disk {disk_idx}\nclean\ncreate partition primary\nformat fs=ntfs quick\nassign\nexit"

        try:
            with open(script_path, "w") as f:
                f.write(script_content)

            # 서브프로세스로 diskpart 실행 (콘솔 창 숨김 처리)
            subprocess.run(
                ["diskpart", "/s", script_path], 
                check=True, 
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            messagebox.showinfo("작업 완료", f"디스크({self.current_disk['Model']}) 초기화 및 포맷이 완료되었습니다.")
            
        except subprocess.CalledProcessError:
            messagebox.showerror("오류", "diskpart 실행 실패. 프로그램이 관리자 권한으로 실행되었는지 확인하십시오.")
        except Exception as e:
            messagebox.showerror("오류", f"알 수 없는 오류 발생:\n{e}")
        finally:
            if os.path.exists(script_path):
                os.remove(script_path)
            self.reset_ui()

    def cancel_and_reset_action(self, event=None):
        if not self.is_waiting_for_user or not self.current_disk:
            return

        self.is_waiting_for_user = False
        messagebox.showinfo("불량 처리", "해당 디스크를 건너뛰고 불량 처리했습니다.")
        self.reset_ui()

    def reset_ui(self):
        self.current_disk = None
        self.is_waiting_for_user = False
        self.label.config(text="디스크 삽입 대기 중...", fg="black")

if __name__ == "__main__":
    root = tk.Tk()
    app = DiskProvisionerApp(root)
    # UI 창을 최상단으로 강제하지 않고 일반 포커스로 띄움
    root.focus_force()
    root.mainloop()
