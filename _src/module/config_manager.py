import configparser

class ConfigManager:
    conf = configparser.ConfigParser()

    def __init__(self,path='config.txt')->None:
        self.path = path
        self.conf.optionxform = str

        for enc in ['utf-8', 'cp949']:
            try:
                self.conf.read(path, encoding=enc)
                return
            except UnicodeDecodeError as e:
                dec_error = f"Failed to decode with encoding {enc}: {e}"
            except Exception as e:
                return print(e)
        return print(dec_error if dec_error else "Unknown error occurred while reading config.")

    def write_conf(self)->None:
        '''현재 conf 내용 파일에 쓰기'''
        with open(self.path, 'w') as configfile:
            self.conf.write(configfile)

    def write_after(func)->None:
        '''함수 실행 후 파일에 저장'''
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            self.write_conf()
            return result
        return wrapper

    @write_after
    def new_item(self,section_name,item:dict)->None:
        '''새 항목 작성'''
        self.new_section(section_name)
        self.conf[section_name].update(item)

    def new_section(self,section_name:str)->None:
        '''secrion_name이 없으면 생성'''
        if not self.conf.has_section(section_name):
            self.conf.add_section(section_name)

    @write_after
    def update_item(self,section_name:str,key:str,new_val)->bool:
        '''기존 항목 값 수정: 기존 여부에 따른 결과 반환'''
        if self.conf.has_section(section_name) and self.conf.has_option(section_name, key):
            self.conf[section_name][key] = new_val
            return True
        else:
            return False

    @write_after
    def delete_item(self,section_name:str,key:str)->None:
        '''항목 삭제'''
        self.conf.remove_option(section_name,key)

    def show_section_items(self, section_name:str)->None:
        '''섹션의 모든 항목을 출력'''
        if self.conf.has_section(section_name):
            print(f"[{section_name}]")
            for key, value in self.conf.items(section_name):
                print(f"{key} = {value}")
        else:
            print(f"Section '{section_name}' does not exist.")

    def get_section_keys(self, section_name:str)->list:
        '''섹션의 모든 키를 리스트로 반환'''
        if self.conf.has_section(section_name):
            return self.conf.options(section_name)
        else:
            print(f"Section '{section_name}' does not exist.")
            return []
        
    def get_section_items(self, section_name:str)->dict:
        '''섹션의 모든 항목을 딕셔너리로 반환'''
        if self.conf.has_section(section_name):
            return dict(self.conf.items(section_name))
        else:
            print(f"Section '{section_name}' does not exist.")
            return {}

    def get_section_vals(self, section_name:str, keys:list) -> list:
        '''섹션의 해당하는 값을 리스트로 반환'''
        if not self.conf.has_section(section_name):
            return []
        return [self.conf.get(section_name, key, fallback=None) for key in keys]
    
if __name__ == '__main__':
    cm = ConfigManager()
    cm.new_item('Database',{'key':'val'})
    