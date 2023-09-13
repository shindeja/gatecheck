
import re

class PolicyCheck(object):
    def __init__(self, attribute, value, allowed_values, check_type, object_id):
        self.attribute = attribute
        self.check_type = check_type
        self.value = value
        self.allowed_values = allowed_values
        self.object_id = object_id

    def exact_match(self):
        if self.value in self.allowed_values: return True
        return False

    def pattern_match(self):
        for p in self.allowed_values:
            if re.search(p, self.value):
                return True
        return False

    def range_check(self):
        low = float(min(self.allowed_values))
        high = float(max(self.allowed_values))
        if float(self.value) >= low and float(self.value) <= high:
            return True
        return False

    def check(self):
        if self.check_type == "exact":
            return self.exact_match()
        if self.check_type == "pattern":
            return self.pattern_match()
        if self.check_type == "range":
            return self.range_check()
        return True

    def __str__(self):
        return "object: {}, attribute: {}, value: {}, allowed_values: {}, check_type: {}".format(self.object_id, self.attribute, self.value, self.allowed_values, self.check_type)

    def __repr__(self):
        return self.__str__()
    
