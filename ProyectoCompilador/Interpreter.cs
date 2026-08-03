using System;
using System.Collections.Generic;

public class Interpreter
{
    private List<Cuadruplo> cuadruplos;
    private Dictionary<string, object> memoria = new Dictionary<string, object>();

    public Interpreter(List<Cuadruplo> cuadruplos)
    {
        this.cuadruplos = cuadruplos;
    }

    public void Ejecutar()
    {
        int pc = 0;

        while (pc < cuadruplos.Count)
        {
            Cuadruplo q = cuadruplos[pc];

            switch (q.Oper)
            {
                case ":=":
                    memoria[q.Resultado] = GetValor(q.Op1);
                    pc++;
                    break;

                case "+":
                    memoria[q.Resultado] = Sumar(GetValor(q.Op1), GetValor(q.Op2));
                    pc++;
                    break;

                case "-":
                    memoria[q.Resultado] = Restar(GetValor(q.Op1), GetValor(q.Op2));
                    pc++;
                    break;

                case "*":
                    memoria[q.Resultado] = Multiplicar(GetValor(q.Op1), GetValor(q.Op2));
                    pc++;
                    break;

                case "/":
                    memoria[q.Resultado] = Dividir(GetValor(q.Op1), GetValor(q.Op2));
                    pc++;
                    break;

                case ">":
                    memoria[q.Resultado] = Convert.ToDouble(GetValor(q.Op1)) > Convert.ToDouble(GetValor(q.Op2));
                    pc++;
                    break;

                case "<":
                    memoria[q.Resultado] = Convert.ToDouble(GetValor(q.Op1)) < Convert.ToDouble(GetValor(q.Op2));
                    pc++;
                    break;

                case ">=":
                    memoria[q.Resultado] = Convert.ToDouble(GetValor(q.Op1)) >= Convert.ToDouble(GetValor(q.Op2));
                    pc++;
                    break;

                case "<=":
                    memoria[q.Resultado] = Convert.ToDouble(GetValor(q.Op1)) <= Convert.ToDouble(GetValor(q.Op2));
                    pc++;
                    break;

                case "==":
                    memoria[q.Resultado] = GetValor(q.Op1).Equals(GetValor(q.Op2));
                    pc++;
                    break;

                case "!=":
                    memoria[q.Resultado] = !GetValor(q.Op1).Equals(GetValor(q.Op2));
                    pc++;
                    break;

                case "and":
                    memoria[q.Resultado] = (bool)GetValor(q.Op1) && (bool)GetValor(q.Op2);
                    pc++;
                    break;

                case "or":
                    memoria[q.Resultado] = (bool)GetValor(q.Op1) || (bool)GetValor(q.Op2);
                    pc++;
                    break;

                case "NEG":
                    object valNeg = GetValor(q.Op1);
                    if (valNeg is int) memoria[q.Resultado] = -(int)valNeg;
                    else               memoria[q.Resultado] = -(double)valNeg;
                    pc++;
                    break;

                case "Print":
                    string salida = GetValor(q.Op1).ToString();
                    if (salida.StartsWith("\"") && salida.EndsWith("\""))
                        salida = salida.Substring(1, salida.Length - 2);
                    Console.WriteLine(salida);
                    pc++;
                    break;

                case "Goto":
                    pc = int.Parse(q.Resultado);
                    break;

                case "GotoFalse":
                    bool cond = (bool)GetValor(q.Op1);
                    if (!cond) pc = int.Parse(q.Resultado);
                    else       pc++;
                    break;

                default:
                    throw new Exception("Operacion desconocida: " + q.Oper);
            }
        }
    }

    private object GetValor(string token)
    {
        if (token.StartsWith("\""))
            return token;

        if (int.TryParse(token, out int entero))
            return entero;

        if (double.TryParse(token, out double flotante))
            return flotante;

        if (memoria.ContainsKey(token))
            return memoria[token];

        return 0;
    }

    private object Sumar(object a, object b)
    {
        if (a is double || b is double)
            return Convert.ToDouble(a) + Convert.ToDouble(b);
        return (int)a + (int)b;
    }

    private object Restar(object a, object b)
    {
        if (a is double || b is double)
            return Convert.ToDouble(a) - Convert.ToDouble(b);
        return (int)a - (int)b;
    }

    private object Multiplicar(object a, object b)
    {
        if (a is double || b is double)
            return Convert.ToDouble(a) * Convert.ToDouble(b);
        return (int)a * (int)b;
    }

    private object Dividir(object a, object b)
    {
        return Convert.ToDouble(a) / Convert.ToDouble(b);
    }
}