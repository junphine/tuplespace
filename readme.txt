 �����Լ��
 
 ��νԪ�飺
 Ԫ�������ڿռ���ڣ����Ա���ָ��name�����ռ�����ƣ�ע�⣺�������Ԫ������ơ�
 
 ��store�����У� nameΪԪ��ռ����ƣ��൱�����ݿ�ı���
 Ԫ������ֶ�Լ����
            tuple[0]ΪԪ���һ�������ռ���Ψһ��������map������Ϊlist������ת��Ϊtuple��������ΪNone
            tuple[1]ΪԪ��ڶ�����������������������Ԫ��ֲ�ʽ�洢��λ�ã�������map������Ϊlist������ת��Ϊtuple��
            	�ڶ���������ΪNone,���ʱ�õ�һ��������
            [0]��[1]��ͬΨһ��ʶһ��Ԫ��
            tuple[2]������ڵĻ�����Ĭ�ϵ������ֶ�,����Ϊmap
 Ԫ��Ƕ�ף�
 	Ŀǰֻ������һ��Ƕ�ף�������(k,l,i,[2,3]),�����֧�ֶ���Ƕ�״���
          
            
 
 �� TSpaceProxy:
 
 def store(self,name,tuple):
 

            
 ���Ԫ��tuple[0]�Ѿ���space�д��ڣ�����false�������쳣������None��
 
            
 def find(self,name,tuple):
 ���ط���ģʽ��Ԫ�飬���tuple[1]�Ǳ�������ֻ����ָ��server_id�ļ�Ⱥ��
 �쳣����None�����Ϊ�գ�����[]
 ��������ʵ����������
 
 
 
 def take(self,name,tuple,timeout):
 ��ȡһ��ƥ��ģʽ��Ԫ�飬����space��ɾ�������timeout�󻹲����ڣ�����None��
 
 ��������ʵ�ֲַ�ʽ��Ϣ����
 
 
 def fetch(self,name,tuple,timeout):
 ��ȡһ��ƥ��Ԫ�飬��������ڣ����timeout�󻹲����ڣ�����None��
 
 ��������ʵ�ֲַ�ʽkey-value�洢��
 
 def remove(self,name,tuple): 
 ɾ��ģʽƥ���Ԫ�顣�ɹ�ɾ������True���쳣����None
 
 ʵ��map-reduce������������������space�д���һ���µ�tuple�ռ�
 
 def map(self,name,func,code):
 	map�Ľ���ᴴ���µ�Ԫ�飬���Ǹ���ԭ�е�Ԫ��

 def filter(self,name,func,code):
 
 def reduce(self,name,func,code,init_value):
 
 
 ���ø߿��ã�
 ����̨���������Ϊ��ͬ��server_id,����Щserver_id��ͬ�Ļ�����Ϊ���ݡ�

 
            
         