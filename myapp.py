from fractions import Fraction
import random
import argparse
import re

random.seed()

def frac_to_str(f: Fraction) -> str:
    """
    Fraction对象转字符串：
    自然数：直接输出 5
    真分数：3/5
    带分数：2'3/8
    """
    if f.denominator == 1:
        return str(f.numerator)
    # 带分数拆分
    integer = f.numerator // f.denominator
    numer = f.numerator % f.denominator
    if integer == 0:
        return f"{numer}/{f.denominator}"
    else:
        return f"{integer}'{numer}/{f.denominator}"

def is_proper_frac(f:Fraction) -> bool:
    """判断是否为真分数：绝对值分子 < 分母"""
    return abs(f.numerator) < abs(f.denominator)

class ExprNode:
    pass

class ValueNode(ExprNode):
    """叶子节点：数值（Fraction）"""
    def __init__(self, val:Fraction):
        self.val = val
    def get_op_count(self):
        return 0
    def to_str(self):
        return frac_to_str(self.val)
    def normalize_key(self):
        # 标准化key，用于去重
        return frac_to_str(self.val)
    def evaluate(self):
        return self.val

class BinaryNode(ExprNode):
    """二元运算节点 + - * /"""
    def __init__(self, op:str, left:ExprNode, right:ExprNode):
        self.op = op
        self.left = left
        self.right = right
        self.op_cnt = left.get_op_count() + right.get_op_count() + 1
    def get_op_count(self):
        return self.op_cnt
    def to_str(self):
        # 生成表达式字符串，自动加括号保证优先级
        l_str = self.left.to_str()
        r_str = self.right.to_str()
        # 简易括号处理，保证运算优先级
        if isinstance(self.left, BinaryNode):
            l_str = f"({l_str})"
        if isinstance(self.right, BinaryNode):
            r_str = f"({r_str})"
        return f"{l_str} {self.op} {r_str}"
    def normalize_key(self):
        """生成标准化字符串key，实现交换律去重：+ * 的左右子树排序"""
        lk = self.left.normalize_key()
        rk = self.right.normalize_key()
        if self.op in ("+", "*"):
            # 加法乘法，对子节点key排序，a+b 和 b+a 得到相同key
            if lk > rk:
                lk, rk = rk, lk
        return f"({self.op},{lk},{rk})"
    def evaluate(self):
        a = self.left.evaluate()
        b = self.right.evaluate()
        if self.op == '+':
            return a + b
        elif self.op == '-':
            return a - b
        elif self.op == '*':
            return a * b
        elif self.op == '/':
            return a / b
        else:
            raise ValueError("invalid op")

def gen_expr(max_range:int, max_ops:int=3) -> ExprNode:
    """
    递归生成表达式
    max_range: -r 参数，数值上限
    max_ops: 最多运算符，固定3
    返回ExprNode；生成时校验规则，不满足返回None
    """
    # 还有剩余运算符名额，随机选：叶子 / 二元运算
    can_binary = max_ops > 0
    if not can_binary or random.random() < 0.45:
        # 生成叶子节点：自然数 或 真分数
        if random.random() < 0.5:
            # 自然数 [0, max_range-1]
            num = random.randint(0, max_range -1)
            return ValueNode(Fraction(num,1))
        else:
            # 真分数：分子 < 分母，分母 <=max_range
            denom = random.randint(2, max_range)
            numer = random.randint(1, denom -1)
            return ValueNode(Fraction(numer, denom))
    else:
        # 生成二元运算，4个运算符随机
        op = random.choice(["+", "-", "*", "/"])
        left_ops = random.randint(0, max_ops -1)
        right_ops = (max_ops -1) - left_ops
        left = gen_expr(max_range, left_ops)
        right = gen_expr(max_range, right_ops)
        if left is None or right is None:
            return None
        node = BinaryNode(op, left, right)
        val = node.evaluate()
        # 规则校验
        if op == '-':
            # 减法：结果不能负数
            if val < 0:
                return None
        if op == '/':
            # 除法结果必须是真分数
            if not is_proper_frac(val):
                return None
        return node

def generate_problem_set(n:int, r:int):
    problems = []
    seen_keys = set() # 存放已经生成题目的标准化key，去重
    while len(problems) < n:
        expr = gen_expr(r, 3)
        if expr is None:
            continue
        key = expr.normalize_key()
        if key in seen_keys:
            continue
        seen_keys.add(key)
        expr_str = expr.to_str() + " ="
        ans = expr.evaluate()
        ans_str = frac_to_str(ans)
        problems.append( (expr_str, ans_str) )
    return problems

def write_files(problems):
    """写入 Exercises.txt 和 Answers.txt"""
    with open("Exercises.txt", "w", encoding="utf-8") as f_ex:
        with open("Answers.txt", "w", encoding="utf-8") as f_an:
            for idx, (prob, ans) in enumerate(problems, start=1):
                f_ex.write(f"{idx}. {prob}\n")
                f_an.write(f"{idx}. {ans}\n")
    print("✅ 生成完成！当前目录生成：Exercises.txt  Answers.txt")

def parse_frac(s:str) -> Fraction:
    """解析带分数字符串，如 2'3/8 → 2+3/8；3/5；5"""
    s = s.strip()
    if "'" in s:
        int_part, frac_part = s.split("'")
        num, den = frac_part.split('/')
        return Fraction(int(int_part),1) + Fraction(int(num), int(den))
    elif '/' in s:
        num, den = s.split('/')
        return Fraction(int(num), int(den))
    else:
        return Fraction(int(s),1)

# ========== 新增：调度场算法，中缀表达式 → 后缀表达式，计算分数结果 ==========
def tokenize(infix_str: str):
    """分词：拆分表达式为token列表，支持带分数、括号、运算符"""
    tokens = []
    i = 0
    s = infix_str.strip()
    while i < len(s):
        ch = s[i]
        if ch in '()+-*/':
            tokens.append(ch)
            i += 1
        elif ch.isdigit() or ch == "'" or ch == '/':
            j = i
            while j < len(s) and (s[j].isdigit() or s[j] in "'/"):
                j += 1
            tokens.append(s[i:j])
            i = j
        elif ch == ' ':
            i += 1
        else:
            i += 1
    return tokens

def shunting_yard(tokens):
    """调度场算法，中缀转后缀"""
    precedence = {'+':1, '-':1, '*':2, '/':2}
    op_stack = []
    postfix = []
    for tok in tokens:
        if tok[0].isdigit():
            postfix.append(tok)
        elif tok == '(':
            op_stack.append(tok)
        elif tok == ')':
            while op_stack and op_stack[-1] != '(':
                postfix.append(op_stack.pop())
            op_stack.pop()
        else:
            while op_stack and op_stack[-1] != '(' and precedence[op_stack[-1]] >= precedence[tok]:
                postfix.append(op_stack.pop())
            op_stack.append(tok)
    while op_stack:
        postfix.append(op_stack.pop())
    return postfix

def calc_postfix(postfix):
    """计算后缀表达式，使用Fraction精确运算"""
    st = []
    for tok in postfix:
        if tok in "+-*/":
            b = st.pop()
            a = st.pop()
            if tok == '+':
                res = a + b
            elif tok == '-':
                res = a - b
            elif tok == '*':
                res = a * b
            elif tok == '/':
                res = a / b
            st.append(res)
        else:
            st.append(parse_frac(tok))
    return st[0]

def calc_expression(expr_text:str) -> Fraction:
    """入口函数：输入表达式字符串，直接计算表达式结果"""
    tokens = tokenize(expr_text)
    post = shunting_yard(tokens)
    return calc_postfix(post)

# ========== 修改后的grade函数：读取题目文件，解析表达式自动算标准答案 ==========
def grade(ex_file:str, ans_file:str):
    correct = []
    wrong = []
    # 读取题目文件
    with open(ex_file, "r", encoding="utf-8") as f:
        ex_lines = f.readlines()
    # 读取学生答案文件
    with open(ans_file, "r", encoding="utf-8") as f:
        ans_lines = f.readlines()

    for idx, ex_line in enumerate(ex_lines, start=1):
        try:
            # 提取题目表达式，去掉编号、末尾等号
            ex_line = ex_line.strip()
            expr_str = re.sub(r'^\d+\.\s*', '', ex_line)
            expr_str = re.sub(r'\s*=$', '', expr_str)
            # 【核心】解析题目式子，自己算出标准答案
            std_frac = calc_expression(expr_str)

            # 读取学生答案
            a_line = ans_lines[idx-1].strip()
            stu_ans_str = re.sub(r'^\d+\.\s*', '', a_line)
            stu_frac = parse_frac(stu_ans_str)

            if stu_frac == std_frac:
                correct.append(idx)
            else:
                wrong.append(idx)
        except Exception:
            wrong.append(idx)

    # 输出Grade.txt
    with open("Grade.txt", "w", encoding="utf-8") as f:
        f.write(f"Correct: {len(correct)} ({','.join(map(str, correct))})\n")
        f.write(f"Wrong: {len(wrong)} ({','.join(map(str, wrong))})\n")
    print("✅ 批改完成！输出 Grade.txt")

def main():
    parser = argparse.ArgumentParser()
    # 生成模式参数
    parser.add_argument("-n", type=int, help="题目数量")
    parser.add_argument("-r", type=int, help="数值范围上限（不包含r）")
    # 判题模式参数
    parser.add_argument("-e", type=str, help="题目文件路径")
    parser.add_argument("-a", type=str, help="学生答案文件路径")
    args = parser.parse_args()
    # 模式判断
    if args.n is not None and args.r is not None:
        # 生成题目模式
        if args.n < 1 or args.n > 10000:
            print("❌ n必须是1~10000之间")
            return
        if args.r < 1:
            print("❌ -r 参数必须≥1")
            return
        probs = generate_problem_set(args.n, args.r)
        write_files(probs)
    elif args.e is not None and args.a is not None:
        # 判题批改模式
        grade(args.e, args.a)
    else:
        print("❌ 参数错误！")
        print("👉 生成题目用法：python myapp.py -n 10 -r 10")
        print("👉 判题用法：python myapp.py -e Exercises.txt -a Answers.txt")

if __name__ == "__main__":
    main()
