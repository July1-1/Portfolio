using System;

class Program
{
    static void Main(string[] args)
    {
        Scanner scanner = new Scanner(args[0]);
        Parser  parser  = new Parser(scanner);

        parser.tabla = new SymbolTable();
        parser.code  = new CodeGen(parser.tabla);

        try
        {
            parser.Parse();
            if (parser.errors.count == 0)
                new Interpreter(parser.code.GetCuadruplos()).Ejecutar();
            else
                Console.WriteLine("Errores sintacticos: " + parser.errors.count);
        }
        catch (Exception ex)
        {
            Console.WriteLine(ex.Message);
        }
    }
}