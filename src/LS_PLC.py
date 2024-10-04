if __debug__:
    import sys
    sys.path.append(r"X:\Github\PLC-Live")
# -------------------------------------------------------------------------------------------
import socket
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
            addr = addr[:2] + 'W' + str(int(addr[3:])//10)
        elif addr_type in ['B','b']: # byte addr
            addr = addr[:2] + 'W' + str(int(addr[3:])*2)
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


# ===========================================================================================
class LS_plc_test():
    def __init__(self):
        self.plc = LS_plc("192.168.0.50")

    def recv_test(self):
        cmd = self.plc._get_xgt_cmd('r',addrs=["%DX5000#01I00"])
        print(cmd)
        # print(cmd.hex())
        recv = self.plc._get_plc_recv(cmd)
        print(recv)
        # print(recv.hex())


# ===========================================================================================
if __name__ == "__main__":
    test = LS_plc_test()
    test.recv_test()
    
