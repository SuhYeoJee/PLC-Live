# PLC-Live
plc 값 화면에 띄워주는 프로그램
을 만드는 템플릿을 자동화

## 개요
PressMonitor를 기반으로 템플릿 자동화
 - LS-PLC
 - read only
 - excel output

### 구조
> MVC 모델

controller: n초 주기로 model의 tick 호출
 - tick 데이터 해석
 - 해석 결과 저장
 - 해석 결과 view로 전달

Model: PLC 값 읽기

View: 전달 받은 값 화면에 표시

> State 모델

각 state별 읽는 주소 상이
 - connect_wait, start_wait, exit_wait

동작 상이
 - view_wait

