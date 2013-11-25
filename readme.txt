 设计契约：
 
 何谓元组：
 元组依赖于空间存在，所以必须指定name，即空间的名称，注意：这个不是元组的名称。
 
 在store方法中， name为元组空间名称，相当于数据库的表名
 元组各个字段约定：
            tuple[0]为元组第一主键，空间中唯一，不能是map（可以为list，但会转化为tuple），不能为None
            tuple[1]为元组第二主键，即分区主键，决定元组分布式存储的位置，不能是map（可以为list，但会转化为tuple）
            	第二主键可以为None,则此时用第一主键分区
            [0]和[1]共同唯一标识一个元组
            tuple[2]如果存在的话，是默认的索引字段,可以为map
 元组嵌套：
 	目前只考虑了一层嵌套，即允许(k,l,i,[2,3]),后面会支持多重嵌套处理
          
            
 
 类 TSpaceProxy:
 
 def store(self,name,tuple):
 

            
 如果元组tuple[0]已经在space中存在，返回false。网络异常，返回None。
 
            
 def find(self,name,tuple):
 返回符合模式的元组，如果tuple[1]非变量，则只检索指定server_id的集群。
 异常返回None，结果为空，返回[]
 可以用来实现搜索引擎
 
 
 
 def take(self,name,tuple,timeout):
 获取一个匹配模式的元组，并从space中删除。如果timeout后还不存在，返回None。
 
 可以用来实现分布式消息队列
 
 
 def fetch(self,name,tuple,timeout):
 获取一个匹配元组，如果不存在，如果timeout后还不存在，返回None。
 
 可以用来实现分布式key-value存储。
 
 def remove(self,name,tuple): 
 删除模式匹配的元组。成功删除返回True，异常返回None
 
 实现map-reduce：这三个函数都会在space中创建一个新的tuple空间
 
 def map(self,name,func,code):
 	map的结果会创造新的元组，而非更改原有的元组

 def filter(self,name,func,code):
 
 def reduce(self,name,func,code,init_value):
 
 
 配置高可用：
 将两台计算机，设为相同的server_id,则这些server_id相同的机器互为备份。

 
            
         