Expr e = new Mul(new Add(new Num(2), new Num(3)), new Num(4));
Console.WriteLine(Eval(e));

static double Eval(Expr e) => e switch
{
    Num(var v) => v,
    Add(var l, var r) => Eval(l) + Eval(r),
    Mul(var l, var r) => Eval(l) * Eval(r),
};

public closed record Expr;
public record Num(double Value) : Expr;
public record Add(Expr Left, Expr Right) : Expr;
public record Mul(Expr Left, Expr Right) : Expr;
