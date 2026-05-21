###User manual and other tricks

### How many error of type missing a `R ...` in the `UserDispo` file

Errors in the `plan` files when a sngle day, th duration is forgotten and the dy does not appear in the GUI.

Examples, in the `UsersDispo` file:

```
4/16/2015  0:0:0  0:0:0  0:0:0  0:0:0  ---------- 0 0
R	86400 1429833600 0 0 0
N	NO:Bordalo
4/18/2015  0:0:0  0:0:0  0:0:0  0:0:0  ---------- 0 0
R	86400 1430611200 0 0 0
N	NO:Guittenny
4/20/2015  0:0:0  0:0:0  0:0:0  0:0:0  ---------- 0 0
R	86400 1429833600 0 0 0
N	NO:Petit
4/26/2015  0:0:0  0:0:0  0:0:0  0:0:0  ---------- 0 0  <---
N	No: portnich                                       <--- No `R` line !
4/29/2015  0:0:0  0:0:0  0:0:0  0:0:0  ---------- 0 0
R	86400 1431129600 0 0 0
N	No:Portnich
5/8/2015  0:0:0  0:0:0  0:0:0  0:0:0  ---------- 0 0
R	86400 1431475200 0 0 0
N	NO: Djurado->IN16
5/12/2015  0:0:0  0:0:0  0:0:0  0:0:0  ---------- 0 0
R	86400 1433030400 0 0 0
N	NO:Bordalo

```



Using `grep`: since the next line is a date instead of a `R` line.

```bash
grep -B1 '^N' UsersDispo |  grep  '\-\-\-\-'
4/26/2015  0:0:0  0:0:0  0:0:0  0:0:0  ---------- 0 0
7/5/2016  0:0:0  0:0:0  0:0:0  0:0:0  ---------- 0 0
12/12/2016  0:0:0  0:0:0  0:0:0  0:0:0  ---------- 0 0
3/25/2024  0:0:0  0:0:0  0:0:0  0:0:0  ---------- 0 0
4/11/2024  0:0:0  0:0:0  0:0:0  0:0:0  ---------- 0 0
6/8/2024  0:0:0  0:0:0  0:0:0  0:0:0  ---------- 0 0
6/6/2025  0:0:0  0:0:0  0:0:0  0:0:0  ---------- 0 0
6/20/2025  0:0:0  0:0:0  0:0:0  0:0:0  ---------- 0 0
(base) ollivier@ollivierlnx2:~/Calendars$ grep -B1 '^N' UsersDispo |  grep  '\-\-\-\-' -c
8
```

