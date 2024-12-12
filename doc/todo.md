# todo

view, PLC 수정

동작 확인

뷰테이블 벌크
 - 아니 테이블 읽은거 어디간거임?
update_data에는 있는데 session.data에는 없어

state.dataset["TABLE_ADDRS"]여기에만 있고 
self.addrs["PLC_ADDR"] 여기에 없어서
state._update_session_data에서 잘림
여기서 table_Addrs순회루프를 새로 만드는게 

뷰테이블 기능
json자동



## 확인사항

- [x] 세션 초기화
- [x] 세션 저장할때 마지막 정보 잘림
- [x] auto 데이터 그래프 갱신시 저장
- [x] 상응하는 그래프 갱신
- [x] 연속 로드하면 알람테이블 계속 길어짐
- [ ] 데이터 시작시 1회 저장
- [ ] 프로그램 270블록 - 24줄
- [ ] LS_PLC connect 실패시 오류처리
- [x] 슬라이더 테이블 연동 안됨
 

# 과제 

1. 듀얼틱 (1초간격읽기, 5초간격읽기 병행)
3. PLC 쓰기동작 작성
4. 모듈화