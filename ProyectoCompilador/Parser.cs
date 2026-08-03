using System;

public class Parser {
	public const int _EOF = 0;
	public const int _ident = 1;
	public const int _entero = 2;
	public const int _flotante = 3;
	public const int _cadena = 4;
	public const int maxT = 42;

	const bool _T = true;
	const bool _x = false;
	const int minErrDist = 2;
	
	public Scanner scanner;
	public Errors  errors;

	public Token t;    // last recognized token
	public Token la;   // lookahead token
	int errDist = minErrDist;

	public SymbolTable tabla;
  	public CodeGen     code;

	public Parser(Scanner scanner) {
		this.scanner = scanner;
		errors = new Errors();
	}

	void SynErr (int n) {
		if (errDist >= minErrDist) errors.SynErr(la.line, la.col, n);
		errDist = 0;
	}

	public void SemErr (string msg) {
		if (errDist >= minErrDist) errors.SemErr(t.line, t.col, msg);
		errDist = 0;
	}
	
	void Get () {
		for (;;) {
			t = la;
			la = scanner.Scan();
			if (la.kind <= maxT) { ++errDist; break; }

			la = t;
		}
	}
	
	void Expect (int n) {
		if (la.kind==n) Get(); else { SynErr(n); }
	}
	
	bool StartOf (int s) {
		return set[s, la.kind];
	}
	
	void ExpectWeak (int n, int follow) {
		if (la.kind == n) Get();
		else {
			SynErr(n);
			while (!StartOf(follow)) Get();
		}
	}


	bool WeakSeparator(int n, int syFol, int repFol) {
		int kind = la.kind;
		if (kind == n) {Get(); return true;}
		else if (StartOf(repFol)) {return false;}
		else {
			SynErr(n);
			while (!(set[syFol, kind] || set[repFol, kind] || set[0, kind])) {
				Get();
				kind = la.kind;
			}
			return StartOf(syFol);
		}
	}

	
	void CompiladorEq6() {
		Expect(5);
		Expect(1);
		Expect(6);
		V();
		Expect(7);
		Expect(8);
		S();
		Expect(9);
		Expect(8);
		Expect(10);
	}

	void V() {
		while (la.kind == 11) {
			Get();
			string tipo = ""; List<string> nombres = new List<string>(); 
			Expect(1);
			nombres.Add(t.val); 
			while (la.kind == 12) {
				Get();
				Expect(1);
				nombres.Add(t.val); 
			}
			Expect(13);
			tipoDato();
			tipo = t.val; 
			foreach(var n in nombres) tabla.Declare(n, tipo); 
			Expect(8);
		}
	}

	void S() {
		while (StartOf(1)) {
			E();
		}
	}

	void tipoDato() {
		if (la.kind == 14) {
			Get();
		} else if (la.kind == 15) {
			Get();
		} else if (la.kind == 16) {
			Get();
		} else if (la.kind == 17) {
			Get();
		} else SynErr(43);
	}

	void E() {
		if (la.kind == 1) {
			ASGNINC();
		} else if (la.kind == 21) {
			W();
		} else if (la.kind == 24) {
			I();
		} else if (la.kind == 27) {
			WH();
		} else if (la.kind == 29) {
			F();
		} else SynErr(44);
	}

	void ASGNINC() {
		Expect(1);
		string nombre = t.val; tabla.Check(nombre); 
		if (la.kind == 18) {
			Get();
			EX();
			code.FinExpresion(); code.Assign(nombre); 
		} else if (la.kind == 19) {
			Get();
			code.PushOperando(nombre, tabla.GetType(nombre));
			code.PushOperando("1", "int");
			code.PushSumaOr("+");
			code.FinExpresion();
			code.Assign(nombre); 
		} else if (la.kind == 20) {
			Get();
			code.PushOperando(nombre, tabla.GetType(nombre));
			code.PushOperando("1", "int");
			code.PushSumaOr("-");
			code.FinExpresion();
			code.Assign(nombre); 
		} else SynErr(45);
		Expect(8);
	}

	void W() {
		Expect(21);
		Expect(22);
		EX();
		code.FinExpresion(); code.Write(); 
		Expect(23);
		Expect(8);
	}

	void I() {
		Expect(24);
		Expect(22);
		EX();
		code.FinExpresion(); code.IfCondicion(); 
		Expect(23);
		Expect(25);
		Expect(6);
		S();
		Expect(10);
		if (la.kind == 26) {
			Get();
			code.ElseInicio(); 
			Expect(6);
			S();
			Expect(10);
			code.ElseFin(); 
		} else if (StartOf(2)) {
			code.IfFin(); 
		} else SynErr(46);
	}

	void WH() {
		Expect(27);
		code.WhileInicio(); 
		Expect(22);
		EX();
		code.FinExpresion(); code.WhileCondicion(); 
		Expect(23);
		Expect(28);
		Expect(6);
		S();
		Expect(10);
		code.WhileFin(); 
	}

	void F() {
		Expect(29);
		Expect(22);
		Expect(1);
		string nombre = t.val; tabla.Check(nombre); 
		Expect(18);
		EX();
		code.FinExpresion(); code.Assign(nombre); 
		Expect(8);
		code.ForInicio(); 
		EX();
		code.FinExpresion(); code.ForCondicion(); 
		Expect(8);
		code.ForGuardaIncremento(); 
		INCF();
		code.ForFinIncremento(); 
		Expect(23);
		Expect(6);
		S();
		Expect(10);
		code.ForFin(); 
	}

	void EX() {
		ER();
		while (la.kind == 30 || la.kind == 31) {
			if (la.kind == 30) {
				Get();
				code.PushMultAnd("and"); 
			} else {
				Get();
				code.PushSumaOr("or");   
			}
			ER();
		}
	}

	void INCF() {
		Expect(1);
		string nombre = t.val; tabla.Check(nombre); 
		if (la.kind == 19) {
			Get();
			code.PushOperando(nombre, tabla.GetType(nombre));
			code.PushOperando("1", "int");
			code.PushSumaOr("+");
			code.FinExpresion();
			code.Assign(nombre); 
		} else if (la.kind == 20) {
			Get();
			code.PushOperando(nombre, tabla.GetType(nombre));
			code.PushOperando("1", "int");
			code.PushSumaOr("-");
			code.FinExpresion();
			code.Assign(nombre); 
		} else SynErr(47);
	}

	void ER() {
		EA();
		if (StartOf(3)) {
			switch (la.kind) {
			case 32: {
				Get();
				code.PushRelacional("<");  
				break;
			}
			case 33: {
				Get();
				code.PushRelacional(">");  
				break;
			}
			case 34: {
				Get();
				code.PushRelacional("<="); 
				break;
			}
			case 35: {
				Get();
				code.PushRelacional(">="); 
				break;
			}
			case 36: {
				Get();
				code.PushRelacional("=="); 
				break;
			}
			case 37: {
				Get();
				code.PushRelacional("!="); 
				break;
			}
			}
			EA();
		}
	}

	void EA() {
		TM();
		while (la.kind == 38 || la.kind == 39) {
			if (la.kind == 38) {
				Get();
				code.PushSumaOr("+"); 
			} else {
				Get();
				code.PushSumaOr("-"); 
			}
			TM();
		}
	}

	void TM() {
		FC();
		while (la.kind == 40 || la.kind == 41) {
			if (la.kind == 40) {
				Get();
				code.PushMultAnd("*"); 
			} else {
				Get();
				code.PushMultAnd("/"); 
			}
			FC();
		}
	}

	void FC() {
		switch (la.kind) {
		case 1: {
			Get();
			tabla.Check(t.val);
			string tipo = tabla.GetType(t.val);
			code.PushOperando(t.val, tipo);     
			break;
		}
		case 2: {
			Get();
			code.PushOperando(t.val, "int");    
			break;
		}
		case 3: {
			Get();
			code.PushOperando(t.val, "float");  
			break;
		}
		case 4: {
			Get();
			code.PushOperando(t.val, "string"); 
			break;
		}
		case 22: {
			Get();
			code.PushFondoFalso(); 
			EX();
			Expect(23);
			code.PopFondoFalso();  
			break;
		}
		case 39: {
			Get();
			FC();
			code.PushSumaOr("NEG"); 
			break;
		}
		default: SynErr(48); break;
		}
	}



	public void Parse() {
		la = new Token();
		la.val = "";		
		Get();
		CompiladorEq6();
		Expect(0);

	}
	
	static readonly bool[,] set = {
		{_T,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x},
		{_x,_T,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_T,_x,_x, _T,_x,_x,_T, _x,_T,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x},
		{_x,_T,_x,_x, _x,_x,_x,_x, _x,_T,_T,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_T,_x,_x, _T,_x,_x,_T, _x,_T,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x},
		{_x,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _x,_x,_x,_x, _T,_T,_T,_T, _T,_T,_x,_x, _x,_x,_x,_x}

	};
} // end Parser


public class Errors {
	public int count = 0;                                    // number of errors detected
	public System.IO.TextWriter errorStream = Console.Out;   // error messages go to this stream
	public string errMsgFormat = "-- line {0} col {1}: {2}"; // 0=line, 1=column, 2=text

	public virtual void SynErr (int line, int col, int n) {
		string s;
		switch (n) {
			case 0: s = "EOF expected"; break;
			case 1: s = "ident expected"; break;
			case 2: s = "entero expected"; break;
			case 3: s = "flotante expected"; break;
			case 4: s = "cadena expected"; break;
			case 5: s = "\"program\" expected"; break;
			case 6: s = "\"{\" expected"; break;
			case 7: s = "\"begin\" expected"; break;
			case 8: s = "\";\" expected"; break;
			case 9: s = "\"end\" expected"; break;
			case 10: s = "\"}\" expected"; break;
			case 11: s = "\"var\" expected"; break;
			case 12: s = "\",\" expected"; break;
			case 13: s = "\":\" expected"; break;
			case 14: s = "\"int\" expected"; break;
			case 15: s = "\"float\" expected"; break;
			case 16: s = "\"bool\" expected"; break;
			case 17: s = "\"string\" expected"; break;
			case 18: s = "\":=\" expected"; break;
			case 19: s = "\"++\" expected"; break;
			case 20: s = "\"--\" expected"; break;
			case 21: s = "\"write\" expected"; break;
			case 22: s = "\"(\" expected"; break;
			case 23: s = "\")\" expected"; break;
			case 24: s = "\"if\" expected"; break;
			case 25: s = "\"then\" expected"; break;
			case 26: s = "\"else\" expected"; break;
			case 27: s = "\"while\" expected"; break;
			case 28: s = "\"do\" expected"; break;
			case 29: s = "\"for\" expected"; break;
			case 30: s = "\"and\" expected"; break;
			case 31: s = "\"or\" expected"; break;
			case 32: s = "\"<\" expected"; break;
			case 33: s = "\">\" expected"; break;
			case 34: s = "\"<=\" expected"; break;
			case 35: s = "\">=\" expected"; break;
			case 36: s = "\"==\" expected"; break;
			case 37: s = "\"!=\" expected"; break;
			case 38: s = "\"+\" expected"; break;
			case 39: s = "\"-\" expected"; break;
			case 40: s = "\"*\" expected"; break;
			case 41: s = "\"/\" expected"; break;
			case 42: s = "??? expected"; break;
			case 43: s = "invalid tipoDato"; break;
			case 44: s = "invalid E"; break;
			case 45: s = "invalid ASGNINC"; break;
			case 46: s = "invalid I"; break;
			case 47: s = "invalid INCF"; break;
			case 48: s = "invalid FC"; break;

			default: s = "error " + n; break;
		}
		errorStream.WriteLine(errMsgFormat, line, col, s);
		count++;
	}

	public virtual void SemErr (int line, int col, string s) {
		errorStream.WriteLine(errMsgFormat, line, col, s);
		count++;
	}
	
	public virtual void SemErr (string s) {
		errorStream.WriteLine(s);
		count++;
	}
	
	public virtual void Warning (int line, int col, string s) {
		errorStream.WriteLine(errMsgFormat, line, col, s);
	}
	
	public virtual void Warning(string s) {
		errorStream.WriteLine(s);
	}
} // Errors


public class FatalError: Exception {
	public FatalError(string m): base(m) {}
}
