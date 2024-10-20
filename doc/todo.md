# todo

- [x] view 알람, 그래프 함수 작성  
    - [x] 그래프 함수 작성  
    - [x] 알람 함수 작성  


- [ ] ctrl 작성  
    - [x] ctrl.load_data
    - [x] ctrl._slider_update
- [ ] model 수정
    - [?] 테이블 읽기 오류 
        - 테이블 전체를 좌르륵 읽고서 타겟 주소 찾기
        - 아냐 이미 그렇게 일하는데 타겟들이 읽은 주소에 매핑되는게 중요

```_change_mode:connect_wait
{'ALARM_APM_X_ERROR': 'off',
 'ALARM_APM_Y_ERROR': 'off',
 'ALARM_APM_Z_ERROR': 'off',
 'ALARM_EMERGENCY_STOP': 'on',
 'ALARM_SEG_EJECT_CONTINUOUS_NG': 'off',
 'SYSTEM_RUN': 0}
{'ALARM_EMERGENCY_STOP': ['on', '2024-10-20 15:44:13']}
False
```