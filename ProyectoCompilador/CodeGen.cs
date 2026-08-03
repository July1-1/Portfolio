using System;
using System.Collections.Generic;

public class Cuadruplo
{
    public string Oper;
    public string Op1;
    public string Op2;
    public string Resultado;

    public Cuadruplo(string oper, string op1, string op2, string resultado)
    {
        Oper      = oper;
        Op1       = op1;
        Op2       = op2;
        Resultado = resultado;
    }
}

public class CodeGen
{
    private SymbolTable symbolTable;
    private Stack<string> pilaOperadores = new Stack<string>();
    private Stack<string> pilaOperandos  = new Stack<string>();
    private Stack<string> pilaTipos      = new Stack<string>();
    private Stack<int> pilaSaltos = new Stack<int>();
    private List<Cuadruplo> cuadruplos   = new List<Cuadruplo>();
    private List<Cuadruplo> incrementoPendiente = null;
    private int           tempCount      = 0;

    public CodeGen(SymbolTable tabla)
    {
        symbolTable = tabla;
    }

    private string NuevoTemporal()
    {
        return "T" + (++tempCount);
    }

    private int ContadorActual()
    {
        return cuadruplos.Count;
    }

    public void PushOperando(string operando, string tipo)
    {
        pilaOperandos.Push(operando);
        pilaTipos.Push(tipo);
    }

    public void PushSumaOr(string op)
    {
        while (pilaOperadores.Count > 0 &&
               (pilaOperadores.Peek() == "+" || pilaOperadores.Peek() == "-" ||
                pilaOperadores.Peek() == "or" ||
                pilaOperadores.Peek() == "*" || pilaOperadores.Peek() == "/" ||
                pilaOperadores.Peek() == "and"))
        {
            GenerarCuadruplo();
        }
        pilaOperadores.Push(op);
    }

    public void PushMultAnd(string op)
    {
        while (pilaOperadores.Count > 0 &&
               (pilaOperadores.Peek() == "*" || pilaOperadores.Peek() == "/" ||
                pilaOperadores.Peek() == "and"))
        {
            GenerarCuadruplo();
        }
        pilaOperadores.Push(op);
    }

    public void PushRelacional(string op)
    {
        while (pilaOperadores.Count > 0 &&
               (pilaOperadores.Peek() == "*" || pilaOperadores.Peek() == "/" ||
                pilaOperadores.Peek() == "and"))
        {
            GenerarCuadruplo();
        }
        pilaOperadores.Push(op);
    }

    public void PushFondoFalso()
    {
        pilaOperadores.Push("(");
    }

    public void PopFondoFalso()
    {
        while (pilaOperadores.Count > 0 && pilaOperadores.Peek() != "(")
        {
            GenerarCuadruplo();
        }
        if (pilaOperadores.Count > 0)
            pilaOperadores.Pop();
    }

    public void Write()
    {
        string op1 = pilaOperandos.Pop();
        cuadruplos.Add(new Cuadruplo("Print", op1, "-", "-"));
    }

    public void IfCondicion()
    {
        string cond = pilaOperandos.Pop();
        cuadruplos.Add(new Cuadruplo("GotoFalse", cond, "-", "?"));
        pilaSaltos.Push(cuadruplos.Count - 1); 
    }

    public void IfFin()
    {
        int posGotoFalse = pilaSaltos.Pop();
        cuadruplos[posGotoFalse].Resultado = ContadorActual().ToString();
    }

    public void ElseInicio()
    {
        cuadruplos.Add(new Cuadruplo("Goto", "-", "-", "?"));
        int posGoto      = cuadruplos.Count - 1;
        int posGotoFalse = pilaSaltos.Pop();
        cuadruplos[posGotoFalse].Resultado = ContadorActual().ToString();
        pilaSaltos.Push(posGoto);
    }

    public void ElseFin()
    {
        int posGoto = pilaSaltos.Pop();
        cuadruplos[posGoto].Resultado = ContadorActual().ToString();
    }

    public void WhileInicio()
    {
        pilaSaltos.Push(ContadorActual());
    }

    public void WhileCondicion()
    {
        string cond = pilaOperandos.Pop();
        cuadruplos.Add(new Cuadruplo("GotoFalse", cond, "-", "?"));
        pilaSaltos.Push(cuadruplos.Count - 1);
    }

    public void WhileFin()
    {
        int posGotoFalse = pilaSaltos.Pop(); 
        int posInicio    = pilaSaltos.Pop(); 
        cuadruplos.Add(new Cuadruplo("Goto", "-", "-", posInicio.ToString()));
        cuadruplos[posGotoFalse].Resultado = ContadorActual().ToString();
    }

    public void ForInicio()
    {
        pilaSaltos.Push(ContadorActual());
    }

    public void ForCondicion()
    {
        string cond = pilaOperandos.Pop();
        cuadruplos.Add(new Cuadruplo("GotoFalse", cond, "-", "?"));
        pilaSaltos.Push(cuadruplos.Count - 1); 
    }

    public void ForFin()
    {
        if (incrementoPendiente != null)
        {
            cuadruplos.AddRange(incrementoPendiente);
            incrementoPendiente = null;
        }

        int posGotoFalse = pilaSaltos.Pop();
        int posInicio    = pilaSaltos.Pop();
        cuadruplos.Add(new Cuadruplo("Goto", "-", "-", posInicio.ToString()));
        cuadruplos[posGotoFalse].Resultado = ContadorActual().ToString();
    }

    public void ForGuardaIncremento()
    {
        pilaSaltos.Push(ContadorActual());
    }

    public void ForFinIncremento()
    {
        int posInicio = pilaSaltos.Pop();
        int cantidad  = ContadorActual() - posInicio;

        incrementoPendiente = new List<Cuadruplo>(
            cuadruplos.GetRange(posInicio, cantidad)
        );

        cuadruplos.RemoveRange(posInicio, cantidad);
    }

    private void GenerarCuadruplo()
    {
        string oper = pilaOperadores.Pop();
        // Por si existen numeros negativos en las pruebas
        if (oper == "NEG")
        {
            string tipoNeg  = pilaTipos.Pop();
            string opNeg    = pilaOperandos.Pop();
            string resNeg   = NuevoTemporal();
            symbolTable.Declare(resNeg, tipoNeg);
            cuadruplos.Add(new Cuadruplo("NEG", opNeg, "-", resNeg));
            pilaOperandos.Push(resNeg);
            pilaTipos.Push(tipoNeg);
            return;
        }
        string tipo2 = pilaTipos.Pop();
        string tipo1 = pilaTipos.Pop();
        string tipoR;

        if (oper == ">" || oper == "<" || oper == ">=" ||
            oper == "<=" || oper == "==" || oper == "!=")
        {
            if (tipo1 != "int" && tipo1 != "float")
                throw new Exception("Error semantico: operador '" + oper +
                                    "' requiere tipo numerico, se encontro -> " + tipo1);
            if (tipo2 != "int" && tipo2 != "float")
                throw new Exception("Error semantico: operador '" + oper +
                                    "' requiere tipo numerico, se encontro -> " + tipo2);
            tipoR = "bool";
        }
        else if (oper == "and" || oper == "or")
        {
            if (tipo1 != "bool" || tipo2 != "bool")
                throw new Exception("Error semantico: operador '" + oper +
                                    "' requiere tipo bool, se encontro -> " +
                                    tipo1 + " y " + tipo2);
            tipoR = "bool";
        }
        else
        {
            tipoR = symbolTable.CheckTypes(tipo1, tipo2);
        }

        pilaTipos.Push(tipoR);

        string op2    = pilaOperandos.Pop();
        string op1    = pilaOperandos.Pop();
        string result = NuevoTemporal();

        symbolTable.Declare(result, tipoR);
        cuadruplos.Add(new Cuadruplo(oper, op1, op2, result));
        pilaOperandos.Push(result);
    }

    public List<Cuadruplo> GetCuadruplos()
    {
        return cuadruplos;
    }

    public void FinExpresion()
    {
        while (pilaOperadores.Count > 0 && pilaOperadores.Peek() != "(")
        {
            GenerarCuadruplo();
        }
    }

    public void Assign(string resultado)
    {
        string op1 = pilaOperandos.Pop();
        cuadruplos.Add(new Cuadruplo(":=", op1, "-", resultado));
    }

    public void Print()
    {
        Console.WriteLine("\n=== CUADRUPLOS ===");
        Console.WriteLine("{0,-5} {1,-8} {2,-8} {3,-8} {4}",
                        "#", "Oper", "Op1", "Op2", "Resultado");
        Console.WriteLine(new string('-', 40));
        int i = 0; 
        foreach (var q in cuadruplos)
        {
            Console.WriteLine("{0,-5} {1,-8} {2,-8} {3,-8} {4}",
                            i++, q.Oper, q.Op1, q.Op2, q.Resultado);
        }
    }
}