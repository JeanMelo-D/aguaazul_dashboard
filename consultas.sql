SELECT
    T0."CardCode",
    T0."CardName" AS "Razao_Social",
    CASE 
        WHEN T0."CardType" = 'C' THEN 'CLIENTE'
        WHEN T0."CardType" = 'S' THEN 'FORNECEDOR'
        WHEN T0."CardType" = 'L' THEN 'LEAD'
    END AS "TIPO",
    T0."CardType",
    T0."GroupCode",
    T1."GroupName",
    T0."CmpPrivate",
    T0."Address",
    T0."ZipCode",
    T0."MailAddres",
    T0."MailZipCod",
    T0."Balance",
    T0."City",
    T0."County",
    T0."Country"
    
FROM 
    "SBOFAZAGUAAZUL23"."OCRD" T0
    LEFT OUTER JOIN "SBOFAZAGUAAZUL23"."OCRG" T1 ON T0."GroupCode" = T1."GroupCode"
    
WHERE 
    T0."frozenFor" = 'N' 