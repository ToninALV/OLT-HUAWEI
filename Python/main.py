import telnetlib
import os
import time
from datetime import datetime, date

path1 = "C:\Python\service_port_all.txt"
path2 = "C:\Python\onus_offline.txt" 
path3 = "C:\Python\log.txt"

atual_date = date.today()
#atual_hour = datetime.now()
list = []
list_onus_deletadas = []

try:
    os.remove(path1)
    os.remove(path2)
except:
    pass

print(datetime.now())

host = "10.145.17.2"
port = 23

user = b'root\n'
password = b'ip2012frb\n'

telnet = telnetlib.Telnet(host, port, timeout=5)

telnet.read_until(b'name:')
telnet.write(user)

telnet.read_until(b'password:')
telnet.write(password)

telnet.write(b'enable\n')
#telnet.write(b'scroll 512\n')
telnet.write(b'config\n')
telnet.write(b'mmi-mode original-output\n')
telnet.write(b'display service-port all \n\n')
time.sleep(0.2)

data = telnet.read_until(b'Note', timeout=5)

data = data.decode('utf-8')

lines = data.splitlines()

result = '\n'.join(lines)

telnet.write(b'scroll 27\n')


with open(path1, 'w') as arquivo: 
    arquivo.write(result)

arquivo = open(path1, 'r')
for line in arquivo:
    if ("down" in line):
        result = line.split()
        
        service_port_index = result[0]
        
        frame = result[4]
        frame = frame.replace('/', ' ')
        frame = frame.split()
        frame = frame[0]
        
        slot = result[4]
        slot = slot.replace('/', ' ')
        slot = slot.split()
        slot = slot[1]
        
        port_pon = result[5]
        port_pon = port_pon.replace('/', ' ')
        port_pon = port_pon[1:3]

        onu_id = result[6]
                
        list.append((service_port_index, frame, slot, port_pon, onu_id))
        

i = -1
while i < len(list):  
    i += 1
    if i < len(list):
        index = list[i]
        index = index[0]
        
        frame = list[i]
        frame = frame[1]
        
        slot = list[i]
        slot = slot[2]
        
        port_pon = list[i]
        port_pon = port_pon[3]
        
        onu_id = list[i]
        onu_id = onu_id[4]
        
        command = f'display ont info {frame} {slot} {port_pon} {onu_id}'
        command = f'{command}\n\n'.encode('utf-8')

        telnet.write(command)
        telnet.write(b'q\n')
        data = telnet.read_until(b'VoIP', timeout=5)
        data = data.decode('utf-8')

        lines = data.splitlines()
        result = '\n'.join(lines)
        
        with open(path2, 'w') as arquivo:
            arquivo.write(result)
        time.sleep(0.1)
        
        with open(path2, 'r') as arquivo:         
            for line in arquivo:
                if ("SN") in line and ("SN-auth") not in line:
                    result_sn = line.split()
                    result_sn = result_sn[2]
                              
                elif ("Last down time") in line:
                    result = line.split()
                    if result[4] == '-':
                        pass
                        #print(f"Onu a ser deletada de index {index} frame {frame} slot {slot} port {port_pon} onu {onu_id} pois a mesma nunca ficou online.")
                        #list_onus_deletadas.append((result_sn, index, frame, slot, port_pon, onu_id)) 
                    elif result[4] != '-':
                        last_down_time = result[4]
                        last_down_time = datetime.strptime(last_down_time, '%Y-%m-%d').date()
                        diferenca = atual_date - last_down_time 
                        diferenca = str(diferenca)
                        diferenca = diferenca.replace(',', ' ')
                        diferenca = diferenca.split()
                        diferenca = diferenca[0]
                        if diferenca != '0:00:00':
                            diferenca = int(diferenca)         
                            if diferenca >= 45:
                                print(f"Onu a ser deletada de index {index} frame {frame} slot {slot} port {port_pon} onu {onu_id} pois a mesma se encontra a {diferenca} dias down.")
                                list_onus_deletadas.append((result_sn, index, frame, slot, port_pon, onu_id))                     
    else:
        break
   
d = 0
while d < len(list_onus_deletadas):
    if d < len(list):
        
        index = list_onus_deletadas[d]
        index = index[1]
        
        command = f'undo service-port {index}'
        command = f'{command}\n'.encode('utf-8')
        telnet.write(command)
        #print(f"undo service-port {index}")
           
        frame = list_onus_deletadas[d]
        frame = frame[2]
        
        slot = list_onus_deletadas[d]
        slot = slot[3]
        
        port_pon = list_onus_deletadas[d]
        port_pon = port_pon[4]
        
        onu_id = list_onus_deletadas[d]
        onu_id = onu_id[5]
        
        result_sn = list_onus_deletadas[d]
        result_sn = result_sn[0]
        
        #print(f"interface gpon {frame}/{slot}")
        command = f'interface gpon {frame}/{slot}'
        command = f'{command}\n'.encode('utf-8')
        telnet.write(command)
        #print(f"ont delete {port_pon} {onu_id}")
        command = f'ont delete {port_pon} {onu_id}'
        command = f'{command}\n'.encode('utf-8')
        telnet.write(command)
        #print("quit")
        telnet.write(b'quit\n')
        
        data_after = telnet.read_until(b'quit', timeout=5)
        data_after = data_after.decode('utf-8')

        lines = data_after.splitlines()
        result_after = '\n'.join(lines)
        
        hora_delete = datetime.now()
        hora_delete = str(hora_delete)
        hora_delete = hora_delete[0:19]
        
        print("-" *30)
        print("deletando ONU")
        print(result_after)
        print("-" *30)
        
        result = f"OLT {host} ONU DE SERIAL {result_sn} SERVICE_INDEX {index} FRAME {frame} SLOT {slot} PORT {port_pon} ID {onu_id} DELETADA NO DIA {hora_delete}\n"
    
        with open(path3, 'a') as arquivo:
            arquivo.write(result)
            
        d += 1
    else:
        break
   
print(datetime.now())
telnet.close()