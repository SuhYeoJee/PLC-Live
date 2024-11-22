import configparser

# 설정 파일 객체 생성
config = configparser.ConfigParser()
config.optionxform = str
# INI 파일 형식으로 읽기
config.read('./doc/addrs.txt', encoding='utf-8')

# PROGRAM_VIEW 섹션을 읽기
if 'PROGRAM_VIEW' in config:
    for i,w in config['PROGRAM_VIEW'].items():
        il = i.split(',')
        value_type = 'I'
        res = f'%{il[0]}#{il[1]:2}{value_type}{il[-1]:2}'
        print(f"{w}:{res}")
else:
    print('PROGRAM_VIEW 섹션이 없습니다.')
