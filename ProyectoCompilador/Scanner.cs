
using System;
using System.IO;
using System.Collections;


// Representa un simbolo lexico que se encuentra en el codigo fuente. Cada token tiene las caracteristicas
// declaradas en la clase
public class Token {
	public int kind;    // token kind
	public int pos;     // token position in bytes in the source text (starting at 0)
	public int charPos;  // token position in characters in the source text (starting at 0)
	public int col;     // token column (starting at 1)
	public int line;    // token line (starting at 1)
	public string val;  // token value
	public Token next;  // ML 2005-03-11 Tokens are kept in linked list
}

//-----------------------------------------------------------------------------------
// Buffer: Maneja la lectura del archivo fuente como un flujo de bytes
//-----------------------------------------------------------------------------------
public class Buffer {
	// This Buffer supports the following cases:
	// 1) seekable stream (file)
	//    a) whole stream in buffer
	//    b) part of stream in buffer
	// 2) non seekable stream (network, console)

	public const int EOF = char.MaxValue + 1;
	const int MIN_BUFFER_LENGTH = 1024; // 1KB
	const int MAX_BUFFER_LENGTH = MIN_BUFFER_LENGTH * 64; // 64KB
	byte[] buf;         // input buffer
	int bufStart;       // position of first byte in buffer relative to input stream
	int bufLen;         // length of buffer
	int fileLen;        // length of input stream (may change if the stream is no file)
	int bufPos;         // current position in buffer
	Stream stream;      // input stream (seekable)
	bool isUserStream;  // was the stream opened by the user?
	
	// Inicializa el buffer a partir de un stream. Si es un archivo calcula el tamaño y si es en consola incia 
	// con tamaño 0 y va creciendo.
	public Buffer (Stream s, bool isUserStream) {
		stream = s; this.isUserStream = isUserStream;
		
		if (stream.CanSeek) {
			fileLen = (int) stream.Length;
			bufLen = Math.Min(fileLen, MAX_BUFFER_LENGTH);
			bufStart = Int32.MaxValue; // nothing in the buffer so far
		} else {
			fileLen = bufLen = bufStart = 0;
		}

		buf = new byte[(bufLen>0) ? bufLen : MIN_BUFFER_LENGTH];
		if (fileLen > 0) Pos = 0; // setup buffer to position 0 (start)
		else bufPos = 0; // index 0 is already after the file, thus Pos = 0 is invalid
		if (bufLen == fileLen && stream.CanSeek) Close();
	}
	
	// Constructor de copia usado por la otra clase que crea CoCo/R (UTF8Buffer). 
	// Transfiere los campos de este buffer al nuevo, y anula el stream de este 
	// buffer para que el destructor de este buffer no cierre el stream.
	protected Buffer(Buffer b) { // called in UTF8Buffer constructor
		buf = b.buf;
		bufStart = b.bufStart;
		bufLen = b.bufLen;
		fileLen = b.fileLen;
		bufPos = b.bufPos;
		stream = b.stream;
		// keep destructor from closing the stream
		b.stream = null;
		isUserStream = b.isUserStream;
	}

	// Destructor, cierra el stream.
	~Buffer() { Close(); }
	
	// Cierra el stream. Es llamado por el destructor.
	protected void Close() {
		if (!isUserStream && stream != null) {
			stream.Close();
			stream = null;
		}
	}
	
	// Lee el siguiente byte del buffer y avanza la posicion. Si el buffer ya fue leido todo,
	// intenta cargar mas datos del stream.	
	public virtual int Read () {
		if (bufPos < bufLen) {
			return buf[bufPos++];
		} else if (Pos < fileLen) {
			Pos = Pos; // shift buffer start to Pos
			return buf[bufPos++];
		} else if (stream != null && !stream.CanSeek && ReadNextStreamChunk() > 0) {
			return buf[bufPos++];
		} else {
			return EOF;
		}
	}

	// Lee el siguiente byte sin avanzar la posicion. Guarda la posicion actual, llama Read(), y luego
	// restaura la posicion. Es util para ver el siguiente caracter.
	public int Peek () {
		int curPos = Pos;
		int ch = Read();
		Pos = curPos;
		return ch;
	}
	
	// Extrae y devuelve el substring del codigo fuente que va desde beg hasta end, en bytes.
	// beg .. begin, zero-based, inclusive, in byte
	// end .. end, zero-based, exclusive, in byte
	public string GetString (int beg, int end) {
		int len = 0;
		char[] buf = new char[end - beg];
		int oldPos = Pos;
		Pos = beg;
		while (Pos < end) buf[len++] = (char) Read();
		Pos = oldPos;
		return new String(buf, 0, len);
	}

	// Obtiene o establece la posicion actual en el codigo fuente, en bytes. Si se establece 
	// una nueva posicion, el buffer se actualiza automaticamente.
	public int Pos {
		get { return bufPos + bufStart; }
		set {
			if (value >= fileLen && stream != null && !stream.CanSeek) {
				// Wanted position is after buffer and the stream
				// is not seek-able e.g. network or console,
				// thus we have to read the stream manually till
				// the wanted position is in sight.
				while (value >= fileLen && ReadNextStreamChunk() > 0);
			}

			if (value < 0 || value > fileLen) {
				throw new FatalError("buffer out of bounds access, position: " + value);
			}

			if (value >= bufStart && value < bufStart + bufLen) { // already in buffer
				bufPos = value - bufStart;
			} else if (stream != null) { // must be swapped in
				stream.Seek(value, SeekOrigin.Begin);
				bufLen = stream.Read(buf, 0, buf.Length);
				bufStart = value; bufPos = 0;
			} else {
				// set the position to the end of the file, Pos will return fileLen.
				bufPos = fileLen - bufStart;
			}
		}
	}
	
	// Lee el siguiente bloque de datos del stream en el buffer. Devuelve la cantidad de 
	// bytes leidos, o 0 si se ha llegado al final del stream.
	private int ReadNextStreamChunk() {
		int free = buf.Length - bufLen;
		if (free == 0) {
			// in the case of a growing input stream
			// we can neither seek in the stream, nor can we
			// foresee the maximum length, thus we must adapt
			// the buffer size on demand.
			byte[] newBuf = new byte[bufLen * 2];
			Array.Copy(buf, newBuf, bufLen);
			buf = newBuf;
			free = bufLen;
		}
		int read = stream.Read(buf, bufLen, free);
		if (read > 0) {
			fileLen = bufLen = (bufLen + read);
			return read;
		}
		// end of stream reached
		return 0;
	}
}

//-----------------------------------------------------------------------------------
// UTF8Buffer
//-----------------------------------------------------------------------------------
public class UTF8Buffer: Buffer {
	public UTF8Buffer(Buffer b): base(b) {}

	public override int Read() {
		int ch;
		do {
			ch = base.Read();
			// until we find a utf8 start (0xxxxxxx or 11xxxxxx)
		} while ((ch >= 128) && ((ch & 0xC0) != 0xC0) && (ch != EOF));
		if (ch < 128 || ch == EOF) {
			// nothing to do, first 127 chars are the same in ascii and utf8
			// 0xxxxxxx or end of file character
		} else if ((ch & 0xF0) == 0xF0) {
			// 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
			int c1 = ch & 0x07; ch = base.Read();
			int c2 = ch & 0x3F; ch = base.Read();
			int c3 = ch & 0x3F; ch = base.Read();
			int c4 = ch & 0x3F;
			ch = (((((c1 << 6) | c2) << 6) | c3) << 6) | c4;
		} else if ((ch & 0xE0) == 0xE0) {
			// 1110xxxx 10xxxxxx 10xxxxxx
			int c1 = ch & 0x0F; ch = base.Read();
			int c2 = ch & 0x3F; ch = base.Read();
			int c3 = ch & 0x3F;
			ch = (((c1 << 6) | c2) << 6) | c3;
		} else if ((ch & 0xC0) == 0xC0) {
			// 110xxxxx 10xxxxxx
			int c1 = ch & 0x1F; ch = base.Read();
			int c2 = ch & 0x3F;
			ch = (c1 << 6) | c2;
		}
		return ch;
	}
}

//-----------------------------------------------------------------------------------
// Scanner: Analizador lexico generado por Coco/R. Se encarga de leer el codigo fuente 
//y convertirlo en una secuencia de tokens, que seran usados por el parser
//-----------------------------------------------------------------------------------
public class Scanner {
	const char EOL = '\n';
	const int eofSym = 0; /* pdt */
	const int maxT = 42;
	const int noSym = 42;


	public Buffer buffer; // scanner buffer
	
	Token t;          // current token
	int ch;           // current input character
	int pos;          // byte position of current character
	int charPos;      // position by unicode characters starting with 0
	int col;          // column number of current character
	int line;         // line number of current character
	int oldEols;      // EOLs that appeared in a comment;
	static readonly Hashtable start; // maps first token character to start state

	Token tokens;     // list of tokens already peeked (first token is a dummy)
	Token pt;         // current peek token
	
	char[] tval = new char[128]; // text of current token
	int tlen;         // length of current token
	
	// Inicializa la tala de transiciones del automata a partir del primer caracter del token. 
	// El automata se ha generado a partir de la expresion regular de cada token.
	static Scanner() {
		start = new Hashtable(128);
		for (int i = 65; i <= 90; ++i) start[i] = 1;
		for (int i = 97; i <= 122; ++i) start[i] = 1;
		for (int i = 48; i <= 57; ++i) start[i] = 6;
		start[34] = 4; 
		start[123] = 7; 
		start[59] = 8; 
		start[125] = 9; 
		start[44] = 10; 
		start[58] = 24; 
		start[43] = 25; 
		start[45] = 26; 
		start[40] = 14; 
		start[41] = 15; 
		start[60] = 27; 
		start[62] = 28; 
		start[61] = 18; 
		start[33] = 20; 
		start[42] = 22; 
		start[47] = 23; 
		start[Buffer.EOF] = -1;

	}
	
	// Abre el archivo fuente y lo asigna al buffer.
	public Scanner (string fileName) {
		try {
			Stream stream = new FileStream(fileName, FileMode.Open, FileAccess.Read, FileShare.Read);
			buffer = new Buffer(stream, false);
			Init();
		} catch (IOException) {
			throw new FatalError("Cannot open file " + fileName);
		}
	}
	
	// Inicia el scanner a partir de un stream ya abierto, por ejemplo leer el codigo 
	// fuente sin pasar por un archivo necesariamente.
	public Scanner (Stream s) {
		buffer = new Buffer(s, true);
		Init();
	}
	
	// Prepara el estado inicial del scanner, donde reinicia la posicion, linea, columna.
	// Lee el primer caracter y crea el token inicial en la lista enlazada.
	void Init() {
		pos = -1; line = 1; col = 0; charPos = -1;
		oldEols = 0;
		NextCh();
		if (ch == 0xEF) { // check optional byte order mark for UTF-8
			NextCh(); int ch1 = ch;
			NextCh(); int ch2 = ch;
			if (ch1 != 0xBB || ch2 != 0xBF) {
				throw new FatalError(String.Format("illegal byte order mark: EF {0,2:X} {1,2:X}", ch1, ch2));
			}
			buffer = new UTF8Buffer(buffer); col = 0; charPos = -1;
			NextCh();
		}
		pt = tokens = new Token();  // first token is a dummy
	}
	
	// Avanza al siguiente caracter del Buffer y actualiza la linea, columna y posicion.
	void NextCh() {
		if (oldEols > 0) { ch = EOL; oldEols--; } 
		else {
			pos = buffer.Pos;
			// buffer reads unicode chars, if UTF8 has been detected
			ch = buffer.Read(); col++; charPos++;
			// replace isolated '\r' by '\n' in order to make
			// eol handling uniform across Windows, Unix and Mac
			if (ch == '\r' && buffer.Peek() != '\n') ch = EOL;
			if (ch == EOL) { line++; col = 0; }
		}

	}

	// Agrega el caracter actual al token y avanza al siguiente caracter.
	void AddCh() {
		if (tlen >= tval.Length) {
			char[] newBuf = new char[2 * tval.Length];
			Array.Copy(tval, 0, newBuf, 0, tval.Length);
			tval = newBuf;
		}
		if (ch != Buffer.EOF) {
			tval[tlen++] = (char) ch;
			NextCh();
		}
	}

	// Verifica si el identificador recien leido coincide con alguna 
	// palabra reservada, y si es asi, cambia el tipo del token a la palabra reservada.
	void CheckLiteral() {
		switch (t.val) {
			case "program": t.kind = 5; break;
			case "begin": t.kind = 7; break;
			case "end": t.kind = 9; break;
			case "var": t.kind = 11; break;
			case "int": t.kind = 14; break;
			case "float": t.kind = 15; break;
			case "bool": t.kind = 16; break;
			case "string": t.kind = 17; break;
			case "write": t.kind = 21; break;
			case "if": t.kind = 24; break;
			case "then": t.kind = 25; break;
			case "else": t.kind = 26; break;
			case "while": t.kind = 27; break;
			case "do": t.kind = 28; break;
			case "for": t.kind = 29; break;
			case "and": t.kind = 30; break;
			case "or": t.kind = 31; break;
			default: break;
		}
	}

	// Este metodo reconoce y devuelve el siguiente token del codigo fuente. Salta los espacios en blanco y saltos de linea.
	// Consulta la tabla start para ver el estado inicial de acuerdo al caracter actual. Cada switch corresponde a un estado
	// y decide si esperar mas caracteres o ya emitir el token definitivo.
	Token NextToken() {
		while (ch == ' ' ||
			ch >= 9 && ch <= 10 || ch == 13 || ch == ' '
		) NextCh();

		int recKind = noSym;
		int recEnd = pos;
		t = new Token();
		t.pos = pos; t.col = col; t.line = line; t.charPos = charPos;
		int state;
		if (start.ContainsKey(ch)) { state = (int) start[ch]; }
		else { state = 0; }
		tlen = 0; AddCh();
		
		switch (state) {
			case -1: { t.kind = eofSym; break; } // NextCh already done
			case 0: {
				if (recKind != noSym) {
					tlen = recEnd - t.pos;
					SetScannerBehindT();
				}
				t.kind = recKind; break;
			} // NextCh already done
			case 1:
				recEnd = pos; recKind = 1;
				if (ch >= '0' && ch <= '9' || ch >= 'A' && ch <= 'Z' || ch == '_' || ch >= 'a' && ch <= 'z') {AddCh(); goto case 1;}
				else {t.kind = 1; t.val = new String(tval, 0, tlen); CheckLiteral(); return t;}
			case 2:
				if (ch >= '0' && ch <= '9') {AddCh(); goto case 3;}
				else {goto case 0;}
			case 3:
				recEnd = pos; recKind = 3;
				if (ch >= '0' && ch <= '9') {AddCh(); goto case 3;}
				else {t.kind = 3; break;}
			case 4:
				if (ch <= 9 || ch >= 11 && ch <= 12 || ch >= 14 && ch <= '!' || ch >= '#' && ch <= 65535) {AddCh(); goto case 4;}
				else if (ch == '"') {AddCh(); goto case 5;}
				else {goto case 0;}
			case 5:
				{t.kind = 4; break;}
			case 6:
				recEnd = pos; recKind = 2;
				if (ch >= '0' && ch <= '9') {AddCh(); goto case 6;}
				else if (ch == '.') {AddCh(); goto case 2;}
				else {t.kind = 2; break;}
			case 7:
				{t.kind = 6; break;}
			case 8:
				{t.kind = 8; break;}
			case 9:
				{t.kind = 10; break;}
			case 10:
				{t.kind = 12; break;}
			case 11:
				{t.kind = 18; break;}
			case 12:
				{t.kind = 19; break;}
			case 13:
				{t.kind = 20; break;}
			case 14:
				{t.kind = 22; break;}
			case 15:
				{t.kind = 23; break;}
			case 16:
				{t.kind = 34; break;}
			case 17:
				{t.kind = 35; break;}
			case 18:
				if (ch == '=') {AddCh(); goto case 19;}
				else {goto case 0;}
			case 19:
				{t.kind = 36; break;}
			case 20:
				if (ch == '=') {AddCh(); goto case 21;}
				else {goto case 0;}
			case 21:
				{t.kind = 37; break;}
			case 22:
				{t.kind = 40; break;}
			case 23:
				{t.kind = 41; break;}
			case 24:
				recEnd = pos; recKind = 13;
				if (ch == '=') {AddCh(); goto case 11;}
				else {t.kind = 13; break;}
			case 25:
				recEnd = pos; recKind = 38;
				if (ch == '+') {AddCh(); goto case 12;}
				else {t.kind = 38; break;}
			case 26:
				recEnd = pos; recKind = 39;
				if (ch == '-') {AddCh(); goto case 13;}
				else {t.kind = 39; break;}
			case 27:
				recEnd = pos; recKind = 32;
				if (ch == '=') {AddCh(); goto case 16;}
				else {t.kind = 32; break;}
			case 28:
				recEnd = pos; recKind = 33;
				if (ch == '=') {AddCh(); goto case 17;}
				else {t.kind = 33; break;}

		}
		t.val = new String(tval, 0, tlen);
		return t;
	}

	// Se utiliza cuando la maquina de estados avanzo mucho ocupa retroceder.	
	private void SetScannerBehindT() {
		buffer.Pos = t.pos;
		NextCh();
		line = t.line; col = t.col; charPos = t.charPos;
		for (int i = 0; i < tlen; i++) NextCh();
	}
	
	// Devuelve el siguiente token de la secuencia, avanzando en la lista. Si ya hay tokens
	// por un peek, los devuelve en orden sin releer el archivo. Si no hay tokens pendientes,
	// llama a NextToken para obtener el siguiente token del codigo fuente.
	public Token Scan () {
		if (tokens.next == null) {
			return NextToken();
		} else {
			pt = tokens = tokens.next;
			return tokens;
		}
	}

	// Mira hacia adelante en la secuencia de tokens sin consumirlos. Genera nuevos tokens llamando
	// a NextToken si es necesario, y los devuelve en orden. El parser lo usa para tomar decisiones
	// que requieren mas de un token.
	public Token Peek () {
		do {
			if (pt.next == null) {
				pt.next = NextToken();
			}
			pt = pt.next;
		} while (pt.kind > maxT); // skip pragmas
	
		return pt;
	}

	// make sure that peeking starts at the current scan position
	public void ResetPeek () { pt = tokens; }

} // end Scanner
