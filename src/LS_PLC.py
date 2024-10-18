if __debug__:
    import sys
    sys.path.append(r"X:\Github\PLC-Live")
# -------------------------------------------------------------------------------------------
from src.module.queue_plus import QueuePlus
import socket
import re
# ===========================================================================================
BIT         = b'\x00\x00'
BYTE        = b'\x01\x00'
WORD        = b'\x02\x00'
# DOUBLE_WORD = b'\x03\x00'
# LONG_WORD   = b'\x04\x00'
MULTI       = b'\x14\x00'
# ===========================================================================================

class LS_plc():
    def __init__(self,plc_ip:str,port:int=2004):
        self.server_ip = plc_ip
        self.server_port = int(port)
        self.is_connected = False
        self.client_socket = None
    # [연결] ===========================================================================================
    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(3)            
            self.client_socket.connect((self.server_ip, self.server_port))
        except Exception as e:
            print(e)
            # write_error(e)
        else:
            self.is_connected = True
    # --------------------------
    def disconnect(self):
        self.client_socket.close()
        self.is_connected = False
    # --------------------------
    def ensure_connected(func):     # PLC 연결 보장
        def wrapper(self, *args, **kwargs):
            if not self.is_connected:
                self.connect()
            try:
                return func(self, *args, **kwargs)
            finally:
                self.disconnect()
        return wrapper
    # --------------------------
    @ensure_connected
    def _get_plc_recv(self, xgt_cmd:bytes):
        try:
            self.client_socket.sendall(xgt_cmd)
        except Exception as e:
            print(e)
            # write_error(e,console_logging=True)
            return None
        return self.client_socket.recv(1024) #buff
    # [명령어 생성] ===========================================================================================
    def _get_xgt_header(self, cmd_len:int):
        '''
        header                (20)

        CompanyID          (10)
        PLC Info            (2)
        CPU Info            (1)
        Source of Frame     (1)
        Invoke ID           (2)
        Length              (2)
        net_pos             (1)
        BCC                 (1)

        '''
        company_id = b"LSIS-XGT".ljust(10, b'\x00')
        plc_info = b'\x00\x00' # client -> server
        cpu_info = b'\xA0' # XGK
        source_of_frame = b'\x33' # client -> server
        invoke_id = b'\x00\x00'
        length = cmd_len.to_bytes(2,'little')
        net_pos = b'\x00'

        a = company_id + plc_info + cpu_info + source_of_frame + invoke_id + length + net_pos
        bcc = (sum(a) & 0xFF).to_bytes(1, 'little')

        header = a + bcc
        return header
    # --------------------------
    def _addr_to_word_addr(self,addr:str="%DW5004#01I00"):
        '''
        단일 읽기용 주소 변환
        '''
        # DX5004 = DW500.4
        # DBA008 + DBA009 = DW5004
        addr,_,option = addr.partition('#')
        addr_type = addr[2]

        if addr_type in ['X','x']: # bit addr
            word_addr = f"{addr[:2]}W{addr[3:-1]}"
        elif addr_type in ['B','b']: # byte addr
            # word_addr = f"{addr[:2]}W{int(addr[3:], 16)//2:X}"
            word_addr = f"{addr[:2]}W{int(addr[3:], 10)//2}"
        else:
            word_addr = addr

        return word_addr+_+option
    # --------------------------
    def _addr_to_byte_addr(self,addr:str="%DW5004#01I00"):
        '''
        구간 읽기용 주소 변환
        '''
        # DX5004 = DW500.4 = DBA00
        # DW5004 = DBA008, DBA009
        addr, _, option = addr.partition('#')
        addr_type = addr[2]

        if addr_type in ['X', 'x']:  # bit addr
            # byte_addr = f"{addr[:2]}B{int(addr[3:-1],16)*2:X}"
            byte_addr = f"{addr[:2]}B{int(addr[3:-1],10)*2}"
        elif addr_type in ['W', 'w']:  # word addr
            # byte_addr = f"{addr[:2]}B{int(addr[3:], 16)*2:X}" #주소체계
            byte_addr = f"{addr[:2]}B{int(addr[3:], 10)*2}"

        else:
            byte_addr = addr

        return byte_addr + _ + option
    # --------------------------
    def _get_single_read_cmd(self, addrs=["%DB5004#01I00"]):
        '''
        single read     (8 + [2+name])

        op              (2)
        block_type      (2)
        reserve         (2)
        block_length    (2)

        addr_length     (2)
        addr            (name)

        '''
        op = b'\x54\x00' # single read
        data_type = WORD # 단일 읽기 워드로 고정
        blank = b'\x00\x00'
        block_length = len(addrs).to_bytes(2,'little')
        cmd = op + data_type + blank + block_length
        for addr in addrs: 
            word_addr = self._addr_to_word_addr(addr) #word 주소 사용
            word_addr,_,option = word_addr.partition('#')

            addr_length = len(word_addr).to_bytes(2,'little') 
            cmd += (addr_length+ word_addr.encode('ascii'))
        return cmd
    # --------------------------
    def _get_multi_read_cmd(self, addr:str="%DB5004#01I00", size:int=3):
        '''
        multi read (12 +name)
        
        op              (2)
        block_type      (2)
        reserve         (2)
        block_length    (2)

        addr_length     (2)
        addr            (name)        
        data_cnt        (2)
        '''
        op = b'\x54\x00'
        data_type = MULTI #multi의 경우 byte로만 읽기 가능
        blank = b'\x00\x00'
        block_length = b'\x01\x00'
        addr_length = len(addr).to_bytes(2,'little')
        size = size.to_bytes(2,'little')
        byte_addr = self._addr_to_byte_addr(addr) #byte 주소 사용
        byte_addr,_,option = byte_addr.partition('#')

        addr_length = len(byte_addr).to_bytes(2,'little') 
        cmd = op + data_type + blank + block_length + addr_length+ byte_addr.encode('ascii')+ size

        return cmd
    # --------------------------
    def _get_xgt_cmd(self,op,**kwargs)->bytes:
        '''
        전체 명령어 생성기
        op => ["read","r","multi_read","mr",None]
        kwargs => {"r":["addrs"],"mr":["addr","size"],None:["cmd"]}
        '''
        if op in ["read",'r']:
            xgt_cmd = self._get_single_read_cmd(kwargs["addrs"])
        elif op in ['multi_read','mr']:
            xgt_cmd = self._get_multi_read_cmd(kwargs["addr"],kwargs["size"])
        elif "cmd" in kwargs.keys():
            xgt_cmd = kwargs["cmd"]
        else:
            xgt_cmd = b''
        
        xgt_header = self._get_xgt_header(len(xgt_cmd))
        return xgt_header + xgt_cmd
    # [결과 해석] ===========================================================================================
    def _get_read_result(self,recv:bytes,is_multi:bool=False)->QueuePlus:
        recv_body = self._get_recv_body(recv)
        if is_multi:
            result = self._get_multi_read_recvs(recv_body)
        else:
            result = self._get_single_read_recvs(recv_body)
        return result
    # --------------------------
    def _get_recv_body(self, recv:bytes)->bytes:
        '''
        header                (20)

        CompanyID          (10)
        PLC Info            (2)
        CPU Info            (1)
        Source of Frame     (1)
        Invoke ID           (2)
        Length              (2)
        net_pos             (1)
        BCC                 (1)
        '''
        recv_length = int.from_bytes(recv[16:19],'little')
        recv_body = recv[20:21+recv_length]
        return recv_body
    # --------------------------
    def _get_single_read_recvs(self, recv_body:bytes)->QueuePlus:
        '''
        single read     (10 + [2+data_length])

        op                          (2)
        block_type                  (2)
        reserve                     (2)
        error_state                 (2)
        error_info/block_length     (2)

        data_length                 (2)
        data                        (data_length)

        '''

        op = recv_body[:2]
        block_type = recv_body[2:4]
        error_state = recv_body[6:8]
        error_info = recv_body[8:10]
        block_length = int.from_bytes(recv_body[8:10],'little')

        result = QueuePlus()
        idx = 10
        for i in range(block_length):
            data_length = int.from_bytes(recv_body[idx:idx+2],'little')
            data = recv_body[idx+2:idx+2+data_length]
            idx = idx+2+data_length
            result.put(data)

        return result
    # --------------------------
    def _get_multi_read_recvs(self, recv_body:bytes)->QueuePlus:
        '''
        multi read     (12 + [data_length])

        op                          (2)
        block_type                  (2)
        reserve                     (2)
        error_state                 (2)
        error_info/block_length     (2)

        data_cnt                    (2)
        data                        (data_length)
        '''
        op = recv_body[:2]
        block_type = recv_body[2:4]
        error_state = recv_body[6:8]
        error_info = recv_body[8:10]
        block_length = int.from_bytes(recv_body[8:10],'little')
        data_cnt = int.from_bytes(recv_body[10:12],'little')

        result = QueuePlus()
        result.put_list_data([recv_body[12 + idx:12 + idx+1] for idx in range(data_cnt)])
        return result
    # --------------------------
    def _data_decoding(self,datas,addr)->str:
        plc_addr,_,option = addr.partition('#')
        addr_type = plc_addr[2]
        # data_size = int(option[:2])
        data_type = option[2]
        data_scale = int(option[3:])

        if addr_type == 'X': # DX5004 = DW500.4
            idx = int(plc_addr[-1],16) #하위 idx번째 비트
            result = int(''.join(format(byte, '08b') for byte in reversed(datas[0]))[(8*len(datas[0])-1) -idx])
            return result
        elif addr_type == 'B': # DW5004 = DBA008 + DBA009
            if int(plc_addr[-1],16) % 2 == 1:
                datas = [x[1:] for x in datas]
            else: 
                datas = [x[:1] for x in datas]
        else:
            result = None
        data = b''.join(datas)

        if data_type == 'S': # string
            result = re.sub(r'[\x00-\x1F\x7F]', '', data.decode('ASCII'))
        elif data_type == 'I': # unsigned int
            result = int.from_bytes(data,'little') * pow(10,data_scale)
        elif data_type == 'i': # signed int
            result = int.from_bytes(data,'little',signed=True) * pow(10,data_scale)
        elif data_type == 'F': # unsigned float
            result = int.from_bytes(data,'little') / pow(10,data_scale)
        elif data_type == 'f': # signed float
            result = int.from_bytes(data,'little',signed=True) / pow(10,data_scale)
        else:
            result = data.hex()

        return str(result)
    # [호출 함수] ===========================================================================================
    def single_read(self,addrs=["%DW500#01I00","%DW10008#01I00"]):
        cmd = self._get_xgt_cmd('r',addrs=addrs)
        print(cmd)
        print(cmd.hex())
        print('# --------------------------')
        recv = self._get_plc_recv(cmd)
        byte_queue = self._get_read_result(recv)
        result = {}
        for addr in addrs:
            plc_addr,_,option = addr.partition('#')
            data_size = int(option[:2]) or 1

            # byte_queue에서 꺼내서 option에 맞춰서 디코딩
            datas = byte_queue.get_cnt_item(data_size)
            result[plc_addr] = self._data_decoding(datas,addr)
        return result
    # --------------------------
    def multi_read(self,addr="%DX5004#01I00",size=2):
        '''
        addr부터 size만큼 byte 단위 읽기
        return => {'%DBA00': b'M', '%DBA01': b'\xf9'}
        '''
        if addr[2] in ["W","w"]: # word data
            size = size*2
        cmd = self._get_xgt_cmd('mr',addr=addr,size=size)
        recv = self._get_plc_recv(cmd)
        byte_queue = self._get_read_result(recv,True)
        result = {}
        byte_addr = self._addr_to_byte_addr(addr).split('#')[0]
        addr_prefix = byte_addr[:3]
        addr_idx = int(byte_addr[3:],16)

        while not byte_queue.empty():
            result[f'{addr_prefix}{addr_idx:X}'] = byte_queue.get()
            addr_idx += 1
        return result
    # --------------------------
    def table_read(self,addrs:list, start_addr:str, size:int):
        byte_dict = self.multi_read(start_addr, size)
        result = {}
        for addr in addrs:
            plc_addr,_,option = addr.partition('#')
            byte_addr,_,option = self._addr_to_byte_addr(addr).partition('#')

            datas = []
            try:
                datas.append(byte_dict[byte_addr])
                if plc_addr[2] in ['W','w']:
                    byte_addr_idx = f"{byte_addr[:3]}{int(byte_addr[3:],16)+1:X}"
                    datas.append(byte_dict[byte_addr_idx])

                result[plc_addr] = self._data_decoding(datas,addr)
            except Exception as e:
                print(e)
        return result
    # --------------------------
    
    def string_read(self,addr="%DW8090#10S00",size=10): #모니터 프로그램 "10워드들" 고정
        result = {}
        byte_dict = self.multi_read(addr=addr,size=size)
        result[addr] = self._data_decoding(byte_dict.values(),addr)
        return result[addr]
    
    
    def read(self,**kwargs)->dict:
        """
        kwargs
        - single = ["%DW500#01I00","%DW501#01i00","%DW502#01f00"]
        - table = { "addrs":["%DW500#01I00","%DW501#01i00","%DW502#01f00"], "start_addr":"%DW500#01I00", "size": 3}
        """
        try:
            if "single" in kwargs.keys(): #최대 16개 주소 읽기
                string_dict = {addr.split('#')[0]:self.string_read(addr) for addr in kwargs["single"] if 'S' in addr}
                datas = [addr for addr in kwargs["single"] if 'S' not in addr]
                addr_blocks = [datas[i:i + 2] for i in range(0, len(datas), 2)] if datas else []

                results = [self.single_read(addr_block) for addr_block in addr_blocks]
                result = {k: v for d in results for k, v in d.items()}
                result.update(string_dict)

            elif "table" in kwargs.keys(): #연달아 읽기
                result = self.table_read(**kwargs["table"])
            else:
                result = None
        except Exception as e:
            print("***LS_PLC_READ_ERROR***")
            print(e)
            result = None
        finally:
            # print(result)
            return result

# ===========================================================================================
class LS_plc_test():
    def __init__(self):
        self.plc = LS_plc("192.168.0.50")

    def recv_test(self):
        cmd = self.plc._get_xgt_cmd('r',addrs=["%DW500#01I00"])
        print(cmd)
        # print(cmd.hex())
        recv = self.plc._get_plc_recv(cmd)
        print(recv)
        # print(recv.hex())
        res = self.plc._get_read_result(recv)
        while not res.empty():
            print(res.get())

    def single_read_test(self):
        self.plc.single_read(addrs=["%DW5004#01I00","%DW5004#01i00"])
        self.plc.single_read(addrs=["%DBA008#01I00","%DBA009#01I00"])
        self.plc.single_read(addrs=["%DW500#01I00"])
        self.plc.single_read(addrs=["%DX5000#01X00","%DX5001#01X00","%DX500E#01X00","%DX500F#01X00"])

    def mulit_read_test(self):
        self.plc.multi_read(addr="%DX5004#01I00",size=2)
        self.plc.multi_read(addr="%DB5004#01I00",size=4)
        self.plc.multi_read(addr="%DW500#01I00",size=20)

    def table_read_test(self):
        self.plc.table_read(["%DW500#01I00","%DW501#01i00","%DW502#01F00"], "%DW500#01I00",3) # => DBA00,DBA01 / DBA02,DBA03 / DBA04,DBA05
        self.plc.table_read(["%DX5000#01X00","%DX5001#01X00","%DX500F#01X00"], "%DX5000#01I00",3) # => DBA00,DBA01 / DBA02,DBA03 / DBA04,DBA05
        self.plc.table_read(["%DBA00#01X00","%DBA01#01X00","%DBA02#01X00"], "%DBA00#01I00",3) # => DBA00,DBA01 / DBA02,DBA03 / DBA04,DBA05

    def string_read_test(self):
        print(self.plc.string_read("%DW8090#10S00"))
        print(self.plc.string_read("%DW2090#10S00"))

    def read_test(self):
        # self.plc.read(single = ["%DW500#01I00","%DW501#01i00","%DW502#01f00"])
        # self.plc.read(table = { "addrs":["%DW500#01I00","%DW501#01i00","%DW502#01f00"], "start_addr":"%DW500#01I00", "size": 3})
        # self.plc.read(table={"addrs":['%DW2339#00000'],"start_addr":"%DW2100","size":10})
        # self.plc.read(table={"addrs":['%DW2339#00000'],"start_addr":"%DW2110","size":10})
        # self.plc.read(table={"addrs":['%DW2339#00000'],"start_addr":"%DW2330","size":10})
        self.plc.read(single = ["%DW8090#10S00","%DW500#01I00"])

# ===========================================================================================
if __name__ == "__main__":
    test = LS_plc_test()
    # test.single_read_test()
    # test.mulit_read_test()
    # test.table_read_test()
    test.read_test()
    # test.plc.string_read()
    # test.string_read_test()

    