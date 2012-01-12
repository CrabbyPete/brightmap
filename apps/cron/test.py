
import mechanize
import time


class Transaction:
    def run(self):
        self.custom_timers = {}

        br = mechanize.Browser()
        br.set_handle_robots(False)
        
        start_timer = time.time()
        resp = br.open('http://ec2-184-73-32-66.compute-1.amazonaws.com')
        resp.read()
        latency = time.time() - start_timer
        
        form = br.forms()
        
        print form[0]
            
        form[0].username = 'pete.douma@gmail.com'
        form[0].password = 'drd00m'
        print mechanize.urlopen(form.click()).read()
        

    
    
if __name__ == '__main__':
    test = Transaction()
    test.run()