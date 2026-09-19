import argparse
import random
from fractions import Fraction

# 表达式节点基类
class ExprNode:
    def evaluate(self):
        raise NotImplementedError
    def to_string(self):
        raise NotImplementedError

# 数字叶子节点
class ValueNode(ExprNode):
    def __init__(self, val:Fraction):
        self.val = val
    def evaluate(self):
        return self.val
    def to_string(self):
        if self.val.denominator == 1:
            return str(self.val.numerator)
        else:
            return f"{self.val.numerator}/{self.val.denominator}"

# 二元运算节点
class BinOpNode(ExprNode):
    def __init__(self, left:ExprNode, op:str, right:ExprNode):
        self.left = left
        self.op = op
        self.right = right
    def evaluate(self):
        l = self.left.evaluate()
        r = self.right.evaluate()
        if self.op == '+':
            return l + r
        elif self.op == '-':
            return l - r
        elif self.op == '*':
            return l * r
        elif self.op == '/':
            return l / r
        else:
            raise ValueError("invalid operator")
    def to_string(self):
        return f"({self.left.to_string()}{self.op}{self.right.to_string()})"


def gen_expr(max_range:int, max_op_cnt=3):
    if max_op_cnt <=0 or random.random() < 0.4:
        num = random.randint(1, max_range)
        return ValueNode(Fraction(num,1))
    op = random.choice(['+','-','*','/'])
    left = gen_expr(max_range, max_op_cnt-1)
    right = gen_expr(max_range, max_op_cnt-1)
    # 重点：子节点如果是None，直接抛弃当前表达式
    if left is None or right is None:
        return None
    try:
        l_val = left.evaluate()
        r_val = right.evaluate()
        # 减法不能负数
        if op == '-':
            if l_val < r_val:
                return None
        # 除数不能0，除法结果必须是真分数
        if op == '/':
            if r_val == 0:
                return None
            res = l_val / r_val
            if res.numerator >= res.denominator:
                return None
    except ZeroDivisionError:
        return None
    return BinOpNode(left, op, right)


def generate_problem_set(problem_count, max_range):
    expr_list = []
    expr_str_set = set()
    while len(expr_list) < problem_count:
        expr = gen_expr(max_range,3)
        if expr is None:
            continue
        try:
            val = expr.evaluate()
        except ZeroDivisionError:
            continue
        s = expr.to_string()
        if s not in expr_str_set:
            expr_str_set.add(s)
            expr_list.append((s, val))
    return expr_list


def write_exercise_file(problems, ex_path, ans_path):
    with open(ex_path, "w", encoding="utf-8") as fex, open(ans_path, "w", encoding="utf-8") as fans:
        for idx, (expr_str, ans) in enumerate(problems, start=1):
            fex.write(f"{idx}. {expr_str}\n")
            fans.write(f"{idx}. {ans}\n")

def grade(ex_path, ans_path, out_path):
    correct = []
    wrong = []
    # 读取题目
    exprs = []
    with open(ex_path, "r", encoding="utf-8") as f:
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue
            dot_pos = line.find('.')
            exp = line[dot_pos+1:].strip()
            exprs.append(exp)
    # 读取学生答案
    student_ans = []
    with open(ans_path, "r", encoding="utf-8") as f:
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue
            dot_pos = line.find('.')
            a = line[dot_pos+1:].strip()
            student_ans.append(Fraction(a))
    # 判题
    for i, exp_str in enumerate(exprs):
        from ast import parse, NodeVisitor
        class EvalVisitor(NodeVisitor):
            def visit_BinOp(self, node):
                l = self.visit(node.left)
                r = self.visit(node.right)
                t = type(node.op)
                if t.__name__=="Add": return l+r
                elif t.__name__=="Sub": return l-r
                elif t.__name__=="Mult": return l*r
                elif t.__name__=="Div": return l/r
            def visit_Constant(self, node):
                return Fraction(node.value)
        tree = parse(exp_str, mode='eval')
        v = EvalVisitor()
        real_ans = v.visit(tree.body)
        if real_ans == student_ans[i]:
            correct.append(i+1)
        else:
            wrong.append(i+1)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"Correct: {len(correct)} ({','.join(map(str,correct))})\n")
        f.write(f"Wrong: {len(wrong)} ({','.join(map(str,wrong))})\n")
    print("✅ 批改完成！输出 Grade.txt")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=int, help="题目数量")
    parser.add_argument("-r", type=int, help="数字范围上限")
    parser.add_argument("-e", type=str, help="习题文件路径")
    parser.add_argument("-a", type=str, help="答案文件路径")
    args = parser.parse_args()
    if args.n is not None and args.r is not None:
        problems = generate_problem_set(args.n, args.r)
        write_exercise_file(problems, "Exercises.txt", "Answers.txt")
        print("✅ 生成完成！当前目录生成：Exercises.txt  Answers.txt")
    elif args.e is not None and args.a is not None:
        grade(args.e, args.a, "Grade.txt")
    else:
        print("❌ 参数错误！")
        print("👉 生成题目用法：myapp.exe -n 10 -r 10")
        print("👉 判题用法：myapp.exe -e Exercises.txt -a Answers.txt")

if __name__ == "__main__":
    main()
