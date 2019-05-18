class Msg:
  def __init__(self, msg):
    self.msg = msg
  
  def get(self):
    return self.msg
  
  def set(self, msg):
    self.msg = msg
  
