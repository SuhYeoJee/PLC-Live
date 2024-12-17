# todo

- 텍스트 자동생성
    1. table_addr.txt 복사해서 temp.txt에 넣기
    2. make_text.py 실행
    3. addrs.txt에 non_table_addr.txt, temp.txt 이어붙이기
    4. make_json.py 실행

## 확인사항

- [ ] LS_PLC connect 실패시 오류처리
- [ ] 모니터 모드에서 현재 프로그램 1회 표시
    ㄴ 일단 현재 프로그램은 틱당 읽고 나머지는 최초 1회 읽기로 해둠

pyinstaller --onefile main.py

 

# 과제 

1. 듀얼틱 (1초간격읽기, 5초간격읽기 병행)
3. PLC 쓰기동작 작성
4. 모듈화