import queue

class queue_plus(queue.Queue):
    def __init__(self):
        super().__init__()
    
    def put_list_data(self,datas:list):
        [self.put(x) for x in datas]

    def print_all_item(self):
        while not self.empty():
            print(self.get())

    def get_cnt_item(self,cnt:int):
        return [self.get() for _ in range(cnt)]