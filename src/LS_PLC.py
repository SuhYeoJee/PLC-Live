if __debug__:
    import sys
    sys.path.append(r"X:\Github\PLC-Live")
# -------------------------------------------------------------------------------------------
import socket
from module.queue_plus import queue_plus
# from igzg.utils import write_error
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
        addr,_,option = addr.partition('#')
        addr_type = addr[2]

        if addr_type in ['X','x']: # bit addr
            addr = addr[:2] + 'W' + str(addr[3:-1])
        elif addr_type in ['B','b']: # byte addr
            addr = f"{addr[:2]}W{int(addr[3:], 16)//2:X}"
        else:...

        return addr+_+option
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
    """
    def _get_multi_read_cmd(self, addr, size):
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
        data_type = MULTI
        blank = b'\x00\x00'
        block_length = b'\x01\x00'
        addr_length = len(addr).to_bytes(2,'little')
        size = size.to_bytes(2,'little')
        cmd = op + data_type + blank + block_length + addr_length+ addr.encode('ascii')+ size

        return cmd
    """

    def _get_xgt_cmd(self,op,**kwargs):
        if op in ["read",'r']:
            xgt_cmd = self._get_single_read_cmd(kwargs["addrs"])
        elif op in ['multi_read','mr']:...
        
        xgt_header = self._get_xgt_header(len(xgt_cmd))
        return xgt_header + xgt_cmd
    # [결과 해석] ===========================================================================================
    def _get_single_read_result(self,recv:bytes)->queue_plus:
        recv_body = self._get_recv_body(recv)
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
    def _get_single_read_recvs(self, recv_body:bytes)->queue_plus:
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

        result = queue_plus()
        idx = 10
        for i in range(block_length):
            data_length = int.from_bytes(recv_body[idx:idx+2],'little')
            data = recv_body[idx+2:idx+2+data_length]
            idx = idx+2+data_length
            result.put(data)

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
            result = int(''.join(format(byte, '08b') for byte in reversed(datas[0]))[15 - idx])
        elif addr_type == 'B': # DW5004 = DBA008 + DBA009
            if int(plc_addr[-1],16) % 2 == 1:
                datas = [x[:1] for x in datas] # 홀수
            else: 
                datas = [x[1:] for x in datas] # 짝수
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
        else: ...

        return str(result)
    # [호출 함수] ===========================================================================================
    def single_read(self,addrs=["%DW500#01I00","%DW10008#01I00"]):
        cmd = self._get_xgt_cmd('r',addrs=addrs)
        recv = self._get_plc_recv(cmd)
        byte_queue = self._get_single_read_result(recv)
        result = []
        for addr in addrs:
            # byte_queue에서 꺼내서 option에 맞춰서 디코딩
            data_size = int(addr.split('#')[-1][:2])
            datas = byte_queue.get_cnt_item(data_size)
            result.append(self._data_decoding(datas,addr))
        print (result)
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
        res = self.plc._get_single_read_result(recv)
        while not res.empty():
            print(res.get())

    def single_read_test(self):
        self.plc.single_read(addrs=["%DW5004#01I00","%DW5004#01i00"])
        self.plc.single_read(addrs=["%DBA008#01I00","%DBA009#01I00"])
        self.plc.single_read(addrs=["%DW500#01I00"])
        self.plc.single_read(addrs=["%DX5000#01X00","%DX5001#01X00","%DX500E#01X00","%DX500F#01X00"])


# ===========================================================================================
if __name__ == "__main__":
    test = LS_plc_test()
    test.single_read_test()
    
