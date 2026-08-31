from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class PasswordHashPolicy:
    algorithm:str='argon2id'
    memory_cost_kib:int=65536
    time_cost:int=3
    parallelism:int=4
    min_password_length:int=12
    upgrade_on_login:bool=True

    def validate(self):
        if self.algorithm.lower()!='argon2id': raise ValueError('argon2id required')
        if self.memory_cost_kib < 65536: raise ValueError('argon2 memory cost too low')
        if self.time_cost < 2: raise ValueError('argon2 time cost too low')
        if self.parallelism < 1: raise ValueError('argon2 parallelism invalid')
        if self.min_password_length < 12: raise ValueError('minimum password length too low')
        if not self.upgrade_on_login: raise ValueError('hash upgrade-on-login required')
        return self
