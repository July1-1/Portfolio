using System;
using System.Collections.Generic;

public class Symbol
{
    public string Name;
    public string Type;
    public int Address;

    public Symbol(string name, string type, int address)
    {
        Name    = name;
        Type    = type;
        Address = address;
    }
}

public class SymbolTable
{
    private Dictionary<string, Symbol> table = new Dictionary<string, Symbol>();
    private int nextAddress = 0;

    public void Declare(string name, string type)
    {
        if (table.ContainsKey(name))
            throw new Exception("Error semantico: variable ya declarada -> " + name);

        table[name] = new Symbol(name, type, nextAddress++);
    }

    public void Check(string name)
    {
        if (!table.ContainsKey(name))
            throw new Exception("Error semantico: variable no declarada -> " + name);
    }

    public string GetType(string name)
    {
        Check(name);
        return table[name].Type;
    }

    public string CheckTypes(string type1, string type2)
    {
        if (type1 == "int"   && type2 == "int")   return "int";
        if (type1 == "int"   && type2 == "float") return "float";
        if (type1 == "float" && type2 == "int")   return "float";
        if (type1 == "float" && type2 == "float") return "float";
        if (type1 == "bool"  && type2 == "bool")  return "bool";

        throw new Exception("Error semantico: tipos incompatibles -> "
                            + type1 + " y " + type2);
    }

    public void Print()
    {
        Console.WriteLine("\n=== TABLA DE SIMBOLOS ===");
        Console.WriteLine("{0,-15} {1,-10} {2}", "Nombre", "Tipo", "Direccion");
        Console.WriteLine(new string('-', 35));
        foreach (var s in table.Values)
            Console.WriteLine("{0,-15} {1,-10} {2}", s.Name, s.Type, s.Address);
    }
}