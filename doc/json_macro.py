import shutil
import subprocess

# 1. table_addr.txt 복사해서 temp.txt로 저장 (파일이 존재하면 덮어쓰기)
def copy_table_addr_to_temp():
    try:
        shutil.copy('./doc/table_addr.txt', './doc/temp.txt')
        print("table_addr.txt가 temp.txt로 복사되었습니다.")
    except FileNotFoundError:
        print("table_addr.txt 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")

# 2. make_text.py 실행
def run_make_text():
    try:
        subprocess.run(['python', './doc/make_text.py'], check=True)
        print("make_text.py 실행 완료.")
    except subprocess.CalledProcessError:
        print("make_text.py 실행 중 오류 발생.")
    except FileNotFoundError:
        print("make_text.py 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")

# 3. non_table_addr.txt 복사해서 addrs.txt로 저장 (파일이 존재하면 덮어쓰기)
def copy_non_table_addr_to_addrs():
    try:
        shutil.copy('./doc/non_table_addr.txt', './doc/addrs.txt')
        print("non_table_addr.txt가 addrs.txt로 복사되었습니다.")
    except FileNotFoundError:
        print("non_table_addr.txt 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")

# 4. addrs.txt의 뒷부분에 temp.txt의 내용을 이어붙이기
def append_temp_to_addrs():
    try:
        with open('./doc/addrs.txt', 'a') as addrs_file:
            addrs_file.write('\n\n')
            with open('./doc/temp.txt', 'r') as temp_file:
                addrs_file.write(temp_file.read())
        print("temp.txt의 내용이 addrs.txt에 이어졌습니다.")
    except FileNotFoundError:
        print("addrs.txt 또는 temp.txt 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")

# 5. make_json.py 실행
def run_make_json():
    try:
        subprocess.run(['python', './doc/make_json.py'], check=True)
        print("make_json.py 실행 완료.")
    except subprocess.CalledProcessError:
        print("make_json.py 실행 중 오류 발생.")
    except FileNotFoundError:
        print("make_json.py 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")

# 매크로 실행
def run_macro():
    copy_table_addr_to_temp()
    run_make_text()
    copy_non_table_addr_to_addrs()
    append_temp_to_addrs()
    run_make_json()

# 실행
if __name__ == '__main__':
    '''
    - PLC_ADDR.json 자동생성
        1. table_addr.txt 복사해서 temp.txt로 저장.
        2. make_text.py 실행
        3. non_table_addr.txt 복사해서 addrs.txt로 저장.
        3. addrs.txt의 뒷부분에 temp.txt의 내용을 이어붙이기
        4. make_json.py 실행
    '''
    run_macro()
