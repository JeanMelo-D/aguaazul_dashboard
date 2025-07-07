
----
--periodo de produção retornando Hectares Plantados
---
WITH X AS (

 SELECT
    T1."Code" as "PeriodoProd",
	T0."U_CodExterno" as "Safra",
	T1."U_CodTalhao" as "CodTalhao",
    T1."U_DscTalhao" as "Talhao",
    TO_DOUBLE(T1."U_AreaPlanta") AS "HectaresPlantado" ,
    TO_DOUBLE(T1."U_CodExterno") AS "Replantio" ,
	T2."Name" as "Cultura"
	FROM
    "SBOFAZAGUAAZUL23"."@AGRI_PPRO" T0
    INNER JOIN "SBOFAZAGUAAZUL23"."@AGRI_PPRV" T1 ON T0."Code" = T1."Code"
	LEFT OUTER JOIN "SBOFAZAGUAAZUL23"."@AGRI_CTOC" T2 ON T0."U_CodCultura" = T2."Code"
	
	WHERE  T0."U_CodExterno" IS  NOT NULL

)

SELECT 

	"PeriodoProd",
	"Safra",
	"CodTalhao",
	"Talhao",
	"HectaresPlantado",
	"Replantio",
	"Cultura",
	(COALESCE("HectaresPlantado", 0) - COALESCE("Replantio", 0)) AS "Hectares"
	
	
	FROM X
	
	
	Where "HectaresPlantado" > 0 
	 

--------------------------------------------------------------------------
-------------- Boletim de Colheita Puxando Hectares Colhidos -------------
--------------------------------------------------------------------------
WITH X AS (
SELECT
    T0."U_CodPeriodoProducao" as "PeriodoProd",
    T1."U_CodSetor" as "CodSetor",
    T1."U_CodTalhao" as "CodTalhao",
    T2."Name" as "Talhao" ,
    SUM(T1."U_AreaColhida") AS "HectaresColhidos"
FROM
    "SBOFAZAGUAAZUL23"."@AGRI_BOLC" T0
INNER JOIN
    "SBOFAZAGUAAZUL23"."@AGRI_BOLC5" T1 ON T0."DocEntry" = T1."DocEntry"
INNER JOIN
    "SBOFAZAGUAAZUL23"."@AGRI_UNPT" T2 ON T1."U_CodTalhao" = T2."Code"

WHERE T0."Canceled" = 'N'

GROUP BY
    T0."U_CodPeriodoProducao",
    T1."U_CodSetor",
    T1."U_CodTalhao",
    T2."Name"
ORDER BY
    T0."U_CodPeriodoProducao",
    T1."U_CodSetor",
    T1."U_CodTalhao"


)

select * from X


---
---


--------------------------------------------------------------------------
----------------------  Romaneio de Entrada  -----------------------------
--------------------------------------------------------------------------



SELECT
    T1."U_CodPeriodoProducao" as "PeriodoProd",
    T0."U_CodTalhao" as "CodTalhao",
    T9."Name" as "Talhao",
    SUM(T0."U_PesoBruto") AS "PesoCarga",
    SUM(T0."U_PesoTara") AS "PesoTara",
    SUM(T0."U_PesoLiquido") AS "PesoBruto",
    SUM(T0."U_PesoLiquidoDesc") AS "PesoLiquido",
    SUM(T0."U_Diferenca") AS "Desconto"
FROM    "SBOFAZAGUAAZUL23"."@PECU_REGR" T0
INNER JOIN    "SBOFAZAGUAAZUL23"."@AGRI_BOLC" T1 ON T0."U_NumeroBoletim" = T1."U_Numero"
INNER JOIN    "SBOFAZAGUAAZUL23"."@AGRI_UNPT" T9 ON T0."U_CodTalhao" = T9."Code"
WHERE    T0."Canceled" = 'N'
GROUP BY
    T1."U_CodPeriodoProducao",
    T0."U_CodTalhao",
    T9."Name"
ORDER BY
    T1."U_CodPeriodoProducao",
    T0."U_CodTalhao"


