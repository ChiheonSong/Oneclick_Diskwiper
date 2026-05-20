# Oneclick_Diskwiper

중고 저장매체(HDD/SSD) 대량 검수 및 초기화 공정의 병목 현상을 해소하기 위한 1-Click 자동화 파이프라인.
HD Sentinel의 S.M.A.R.T. 검사 데이터를 실시간으로 수신하여, 정상 판정 시 백그라운드에서 `diskpart`를 이용해 즉시 파티션을 초기화합니다.

## 1. System Architecture
* **Data Extraction:** Hard Disk Sentinel Pro (WMI 연동)
* **Logic & UI:** Python 3.x (tkinter, wmi, pywin32)
* **Execution:** Windows 내장 `diskpart` (Subprocess)
* **Trigger:** USB 인터페이스 기반 디스크 삽입 이벤트 (Hot-swap)

## 2. Dependencies & Build
이 스크립트를 `.exe` 파일로 빌드하기 위한 환경 세팅입니다.

### Python 라이브러리 설치
> pip install wmi pywin32 pyinstaller

### 단일 실행 파일(EXE) 빌드 명령어
> pyinstaller --noconsole --onefile disk_provisioner.py
* 생성된 파일은 `dist/` 폴더 내에 위치합니다.

## 3. HD Sentinel Configuration (사전 요구사항)
이 프로그램이 정상 작동하려면 대상 PC에 HD Sentinel Pro가 설치되어 있어야 하며, 다음 설정이 강제됩니다.
1.  **버전 요구사항:** Trial 버전 불가. Pro 버전 오프라인 라이선스 인증 필수.
2.  **WMI 연동:** [설정] -> [고급 옵션] -> **'WMI의 상태 정보 제공'** 체크 활성화.
3.  **백그라운드 실행:** [설정] -> [환경 설정] -> **'Windows 시작 시 실행'** 체크 활성화.

## 4. Operation Guide (작업자 매뉴얼)
1.  빌드된 `disk_provisioner.exe`를 **관리자 권한으로 실행**합니다. (UAC 권한 필수)
2.  USB 도킹 스테이션에 검사할 디스크를 삽입합니다.
3.  화면에 디스크 모델명과 Health 수치(%)가 팝업됩니다.
4.  **[Enter] 키:** 초기화 및 빠른 포맷 진행 (diskpart clean -> format)
5.  **[ESC] 키:** 작업 취소 및 불량 처리(Skip)
6.  작업 완료 알림 확인 후 디스크를 분리합니다.

## 5. Safety 통제 로직
* 운영체제가 설치된 메인 스토리지(SATA/NVMe 등)의 실수 포맷을 방지하기 위해, WMI 기준 `InterfaceType`에 'USB'가 포함된 드라이브만 스캔 및 포맷 대상으로 허용합니다.
