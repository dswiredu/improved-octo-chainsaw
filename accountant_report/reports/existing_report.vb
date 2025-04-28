
Sub q_acntdl()
Dim oldStatusBar As String

Application.ScreenUpdating = False

'Display Progress Bar
ProgressBar.Show

Application.ScreenUpdating = True

End Sub
Sub q_acntdl_rename()


Dim lang As String
Dim filepath As String

filepath = "TEXT;U:\" + Application.UserName + "\Private\Axys\q_acntdl.txt"
    'Gather account specific info from q_acntdl report
    Workbooks("q_acntdl.xls").Worksheets("Sheet1").Activate
    With ActiveSheet.QueryTables.Add(Connection:=filepath, Destination:=Range("A1"))
        .Name = "q_acntdl"
        .FieldNames = True
        .RowNumbers = False
        .FillAdjacentFormulas = False
        .PreserveFormatting = True
        .RefreshOnFileOpen = False
        .RefreshStyle = xlInsertDeleteCells
        .SavePassword = False
        .SaveData = True
        .AdjustColumnWidth = True
        .RefreshPeriod = 0
        .TextFilePromptOnRefresh = False
        .TextFilePlatform = 1252
        .TextFileStartRow = 1
        .TextFileParseType = xlDelimited
        .TextFileTextQualifier = xlTextQualifierDoubleQuote
        .TextFileConsecutiveDelimiter = False
        .TextFileTabDelimiter = True
        .TextFileSemicolonDelimiter = False
        .TextFileCommaDelimiter = False
        .TextFileSpaceDelimiter = False
        .TextFileColumnDataTypes = Array(1)
        .TextFileTrailingMinusNumbers = True
        .Refresh BackgroundQuery:=False
    End With

    Dim mgr As String
    Dim mgrpath As String
    Dim newname As String
    
    mgr = ActiveSheet.Cells(1, 5).Value
    
    Select Case mgr
        Case "ac", "jg_ac", "rc_ac", "rd_ac", "rh_ac"
            mgrpath = "\\server2003\users\chung__a\Accounts\" + ActiveSheet.Cells(1, 3).Value + "1\rep\"
        Case "jg", "rd_jg"
            mgrpath = "\\server2003\users\giacomej\Accounts\" + ActiveSheet.Cells(1, 3).Value + "1\rep\"
        Case "kf", "rd_kf"
            mgrpath = "\\server2003\users\farrantk\Accounts\" + ActiveSheet.Cells(1, 3).Value + "1\rep\"
        Case "vf", "rd_vf", "lc_vf", "sd_vf"
            mgrpath = "\\server2003\users\fourniev\Accounts\" + ActiveSheet.Cells(1, 3).Value + "1\rep\"
        Case "wk", "ef_wk", "bb_wk", "wt_wk"
            mgrpath = "\\server2003\users\kovalchw\Accounts\" + ActiveSheet.Cells(1, 3).Value + "1\rep\"
       ' Case "jb", "jb_ac", "jb_jg", "jb_wk", "jb_kf", "jb_vf"
           ' mgrpath = "\\server2003\users\bruneauj\Accounts\" + ActiveSheet.Cells(1, 3).Value + "1\rep\"
    
    End Select
    
    'Remove bad characters from filename
    newname = Worksheets("q_recon").Range("A2").Value
    newname = Application.WorksheetFunction.Substitute(newname, "<", " ")
    newname = Application.WorksheetFunction.Substitute(newname, ">", " ")
    newname = Application.WorksheetFunction.Substitute(newname, "?", " ")
    newname = Application.WorksheetFunction.Substitute(newname, "[", " ")
    newname = Application.WorksheetFunction.Substitute(newname, "]", " ")
    newname = Application.WorksheetFunction.Substitute(newname, ":", " ")
    newname = Application.WorksheetFunction.Substitute(newname, "|", " ")
    newname = Application.WorksheetFunction.Substitute(newname, "\", " ")
    newname = Application.WorksheetFunction.Substitute(newname, "/", " ")
    newname = Application.WorksheetFunction.Substitute(newname, ".", " ")
        
    'mgrpath = mgrpath + Application.WorksheetFunction.text(Now(), "YYMMDD hhmmss") + "_" + _
                        'newname + " " + LCase(Worksheets("q_recon").Range("A3").Value) + ".xls"

    If Worksheets("q_pvald2").Range("A1").Value = "Évaluation de portefeuille - TRANSACTIONS RÉGLÉES" Then
        lang = "f"
        '05/21/2015: zergounm: Removed "hhmmss", Added Rapport Comptable to file name
        mgrpath = mgrpath + Application.WorksheetFunction.text(Now(), "YYMMDD") + "_Rapport Comptable_" + _
                    newname + " " + LCase(Worksheets("q_recon").Range("A3").Value) + ".xls"
        Worksheets("q_recon").Name = "Réconciliation"
        Worksheets("q_pvald1").Name = "Évaluation - Début"
        Worksheets("q_iedl").Name = "Revenus"
        Worksheets("q_iedl_ann3").Name = "Taxprep - Annexe 3"
        Worksheets("q_rglsdl").Name = "Gains-pertes réalisés"
        Worksheets("q_rglsdl_ann6").Name = "Taxprep - Annexe 6"
        Worksheets("q_rglfdl").Name = "Gains-pertes sur change"
        Worksheets("q_dpwddl").Name = "Dépôts-Retraits-Frais"
        Worksheets("q_bysldl").Name = "Transactions sur compte capital"
        Worksheets("q_nctrdl").Name = "Transactions sans encaisse"
        Worksheets("q_pvald2").Name = "Évaluation - Fin"
        Sheets(Array("Réconciliation", "Évaluation - Début", "Revenus", "Gains-pertes réalisés", _
                        "Gains-pertes sur change", "Dépôts-Retraits-Frais", "Transactions sur compte capital", _
                            "Transactions sans encaisse", "Évaluation - Fin", "Taxprep - Annexe 3", "Taxprep - Annexe 6")).Move
    ElseIf Worksheets("q_pvald2").Range("A1").Value = "Portfolio Valuation - SETTLED TRADES" Then
        lang = "e"
        '05/21/2015: zergounm: Removed "hhmmss", Added Accountant Repor to file name
        mgrpath = mgrpath + Application.WorksheetFunction.text(Now(), "YYMMDD") + "_Accountant Report_" + _
                    newname + " " + LCase(Worksheets("q_recon").Range("A3").Value) + ".xls"
        Worksheets("q_recon").Name = "Reconciliation"
        Worksheets("q_pvald1").Name = "Evaluation - Beginning"
        Worksheets("q_iedl").Name = "Income"
        Worksheets("q_iedl_ann3").Name = "Taxprep - Schedule 3"
        Worksheets("q_rglsdl").Name = "Realized Gains-Losses"
        Worksheets("q_rglsdl_ann6").Name = "Taxprep - Schedule 6"
        Worksheets("q_rglfdl").Name = "Realized Gains-Losses FX"
        Worksheets("q_dpwddl").Name = "Deposits-Withdrawals-Fees"
        Worksheets("q_bysldl").Name = "Capital Transactions"
        Worksheets("q_nctrdl").Name = "Non-cash Transactions"
        Worksheets("q_pvald2").Name = "Evaluation - End"
        Sheets(Array("Reconciliation", "Evaluation - Beginning", "Income", "Realized Gains-Losses", _
                        "Realized Gains-Losses FX", "Deposits-Withdrawals-Fees", "Capital Transactions", _
                            "Non-cash Transactions", "Evaluation - End", "Taxprep - Schedule 3", "Taxprep - Schedule 6")).Move
    End If
    
    Application.DisplayAlerts = False
    ActiveWorkbook.SaveAs Filename:=mgrpath, _
        FileFormat:=xlNormal, Password:="", WriteResPassword:="", _
        ReadOnlyRecommended:=False, CreateBackup:=False
    Application.DisplayAlerts = True
    
    MsgBox "Le fichier a été sauvegardé à cet endroit:" & vbCr & _
            "The file has been saved at the following location:" & vbCr & _
            mgrpath, vbOKOnly, "Lieu de sauvegarde / Save path"
    Workbooks("q_acntdl.xls").Close False
End Sub

Sub q_acntdl_summary()

'Figure out the language of the current portfolio
Dim lang As String
Dim gainloss_label As String
Dim balance_begin_label As String
Dim balance_end_label As String
Dim summary_page_title As String
Dim summary_page_period As String
Dim grand_total_beg_label As String
Dim cash_total_beg_addresses As String
Dim investments_total_beg_addresses As String
Dim portfoliototal_total_beg_addresses As String
Dim grand_total_end_label As String
Dim cash_total_end_addresses As String
Dim investments_total_end_addresses As String
Dim portfoliototal_total_end_addresses As String
Dim cash_verification_addresses As String
Dim investments_verification_addresses As String
Dim portfoliototal_verification_addresses As String
Dim loccur_label1 As String
Dim loccur_label2 As String
Dim repcur_label1 As String
Dim repcur_label2 As String

If Worksheets("q_pvald2").Range("A1").Value = "Évaluation de portefeuille - TRANSACTIONS RÉGLÉES" Then
    lang = "f"
    gainloss_label = "Gain/perte sur change"
    balance_begin_label = "Balance - Début"
    balance_end_label = "Balance - Fin"
    summary_page_title = "Réconciliation de l'activité durant la période"
    summary_page_period = "Du" + Worksheets("q_pvald1").Range("A3").Value + _
                            " au" + Worksheets("q_pvald2").Range("A3").Value
    loccur_label1 = "Monnaie"
    loccur_label2 = "d'origine"
    repcur_label1 = "Monnaie de"
    repcur_label2 = "référence"
    grand_total_beg_label = "Grand Total - Début"
    grand_total_end_label = "Grand Total - Fin"
    verification_label = "Vérification"
    cash_label = "Encaisse"
    asset_label = "Placements"
    total_portfolio_label = "Total du portefeuille"
ElseIf Worksheets("q_pvald2").Range("A1").Value = "Portfolio Valuation - SETTLED TRADES" Then
    lang = "e"
    gainloss_label = "Gain/loss on foreign exchange"
    balance_begin_label = "Balance - Beginning"
    balance_end_label = "Balance - End"
    summary_page_title = "Period Activity Reconciliation"
    summary_page_period = "From" + Worksheets("q_pvald1").Range("A3").Value + _
                            " To" + Worksheets("q_pvald2").Range("A3").Value
    loccur_label1 = "Local"
    loccur_label2 = "Currency"
    repcur_label1 = "Reference"
    repcur_label2 = "Currency"
    grand_total_beg_label = "Grand Total - Beginning"
    grand_total_end_label = "Grand Total - End"
    verification_label = "Verification"
    cash_label = "Cash"
    asset_label = "Investments"
    total_portfolio_label = "Total Portfolio"
End If

'Add the summary worksheet
Workbooks("q_acntdl.xls").Worksheets.Add
ActiveSheet.Name = "q_recon"

    Dim currency_array(19) As String
    'Counter to keep track of how many distinct currencies have been found thus far
    Dim currency_count As Integer
    currency_count = 0

    'Variable to establish if the found currency is already in the array
    Dim have_currency As Boolean
    'Counter to loop through the currency array
    Dim i As Integer
'lang = "f"
'If lang = "f" Then



q_pvald1:
    'Gather list of currency accounts showing up in q_pvald1 report
    Worksheets("q_pvald1").Activate
    Range("A9").Select
    
    'Look for other currency totals by scanning column A
    Do While ActiveCell.Row <> 65536
        'If the header is a total header, skip loop to next header
        If UCase(Left(ActiveCell.Value, 8)) <> "TOTAL - " Then GoTo end_of_q_pvald1_loop
        
        'Assign default values to declared variables
        have_currency = False   'Assume currencies have not been found
        i = 0                   'Set to 0 to loop through the array
        For i = 0 To currency_count - 1
            If currency_array(i) <> "" And ActiveCell.Value = currency_array(i) Then have_currency = True
        Next
        If have_currency = False Then
            currency_array(currency_count) = ActiveCell.Value
            currency_count = currency_count + 1
        End If
       ' MsgBox (currency_count)
end_of_q_pvald1_loop:
        'Scan down the column for next header
        Selection.End(xlDown).Select
    Loop
    Worksheets("q_pvald1").Range("A1").Select
    
    
    
 ''''''''''''' 06/11/2014: zergounm : Added currency scan to q_pvald2
q_pvald2:
    'Gather list of currency accounts showing up in q_pvald2 report
    Worksheets("q_pvald2").Activate
    Range("A9").Select
    
    'Look for other currency totals by scanning column A
    Do While ActiveCell.Row <> 65536
        'If the header is a total header, skip loop to next header
        If UCase(Left(ActiveCell.Value, 8)) <> "TOTAL - " Then GoTo end_of_q_pvald2_loop
        
        'Assign default values to declared variables
        have_currency = False   'Assume currencies have not been found
        i = 0                   'Set to 0 to loop through the array
        For i = 0 To currency_count - 1
            If currency_array(i) <> "" And ActiveCell.Value = currency_array(i) Then have_currency = True
        Next
        If have_currency = False Then
            currency_array(currency_count) = ActiveCell.Value
            currency_count = currency_count + 1
        End If
        'MsgBox (currency_count)
end_of_q_pvald2_loop:
        'Scan down the column for next header
        Selection.End(xlDown).Select
    Loop
    Worksheets("q_pvald2").Range("A1").Select
                
q_iedl:
    
    'Gather list of currency accounts showing up in q_iedl report
    Worksheets("q_iedl").Activate
    Range("B9").Select
    
    'Grab the first currency located at cell B9 or go to next report report
    If ActiveCell.Value = "" Then GoTo q_dpwddl
    'Counter to keep track of how many distinct currencies have been found thus far
    
    'Look for other currencies by scanning column B
    Do While ActiveCell.Row <> 65536
        'If the header is a total header, skip loop to next header
        If UCase(Left(ActiveCell.Value, 8)) <> "TOTAL - " Then GoTo end_of_q_iedl_loop
        
        'Assign default values to declared variables
        have_currency = False   'Assume currencies have not been found
        i = 0                   'Set to 0 to loop through the array
        For i = 0 To currency_count - 1
            If currency_array(i) <> "" And ActiveCell.Value = currency_array(i) Then have_currency = True
        Next
        If have_currency = False Then
            currency_array(currency_count) = ActiveCell.Value
            currency_count = currency_count + 1
        End If
end_of_q_iedl_loop:
        'Scan down the column for next header
        Selection.End(xlDown).Select
    Loop
    Worksheets("q_iedl").Range("A1").Select

q_dpwddl:
    'Gather list of currency accounts showing up in q_dpwddl report
    Worksheets("q_dpwddl").Activate
    Range("A8").Select
    
    'Grab the first currency located at cell B9 or go to next report report
    If ActiveCell.Value = "" Then
        GoTo q_bysldl
    Else
        Selection.End(xlDown).Select
    End If
    
    'Counter to keep track of how many distinct currencies have been found thus far
    
    'Look for other currencies by scanning column B
    Do While ActiveCell.Row <> 65536
        'Assign default values to declared variables
        have_currency = False   'Assume currencies have not been found
        i = 0                   'Set to 0 to loop through the array
        For i = 0 To currency_count - 1
            If currency_array(i) <> "" And ActiveCell.Value = currency_array(i) Then have_currency = True
        Next
        If have_currency = False Then
            currency_array(currency_count) = ActiveCell.Value
            currency_count = currency_count + 1
        End If
end_of_q_dpwddl_loop:
        'Scan down the column for next header
        Selection.End(xlDown).Select
        Selection.End(xlDown).Select
    Loop
    Worksheets("q_dpwddl").Range("A1").Select

q_bysldl:
    'Gather list of currency accounts showing up in q_iedl report
    Worksheets("q_bysldl").Activate
    Range("A10").Select
    
    'Grab the first currency located at cell A9 or go to next report report
    If ActiveCell.Value = "" Then GoTo q_nctrdl
    'Counter to keep track of how many distinct currencies have been found thus far
    
    'Look for other currencies by scanning column B
    Do While ActiveCell.Row <> 65536
        'If the header is a total header, skip loop to next header
        If UCase(Left(ActiveCell.Value, 8)) <> "TOTAL - " Then GoTo end_of_q_bysldl_loop
        
        'Assign default values to declared variables
        have_currency = False   'Assume currencies have not been found
        i = 0                   'Set to 0 to loop through the array
        For i = 0 To currency_count - 1
            If currency_array(i) <> "" And ActiveCell.Value = currency_array(i) Then have_currency = True
        Next
        If have_currency = False Then
            currency_array(currency_count) = ActiveCell.Value
            currency_count = currency_count + 1
        End If
end_of_q_bysldl_loop:
        'Scan down the column for next header
        Selection.End(xlDown).Select
    Loop
    Worksheets("q_bysldl").Range("A1").Select

q_nctrdl:
    'Gather list of currency accounts showing up in q_dpwddl report
    Worksheets("q_nctrdl").Activate
    Range("A10").Select
    
    'Grab the first currency located at cell B9 or go to next report report
    If ActiveCell.Value = "" Then GoTo end_of_currency_loop
    'Counter to keep track of how many distinct currencies have been found thus far
    
    'Look for other currencies by scanning column B
    Do While ActiveCell.Row <> 65536
        'Assign default values to declared variables
        have_currency = False   'Assume currencies have not been found
        i = 0                   'Set to 0 to loop through the array
        For i = 0 To currency_count - 1
            If currency_array(i) <> "" And ActiveCell.Value = currency_array(i) Then have_currency = True
        Next
        If have_currency = False Then
            currency_array(currency_count) = ActiveCell.Value
            currency_count = currency_count + 1
        End If
end_of_q_nctrdl_loop:
        'Scan down the column for next header
        Selection.End(xlDown).Select
Loop
    Worksheets("q_nctrdl").Range("A1").Select
    

        
end_of_currency_loop:
'/////////PRINT OUT ARRAY CONTENT
        
        'Printout currency_array content
        i = 0
        Dim j As Integer
        j = 11
        For i = 0 To 19
            If currency_array(i) = "" Then Exit For
            Worksheets("q_recon").Cells(j, 1).Value = Right(currency_array(i), Len(currency_array(i)) - 8)
            
            'Scan q_pvald1
            Worksheets("q_pvald1").Activate
            With ActiveSheet.Columns("E:E")
                Set c = .Find(Right(currency_array(i), Len(currency_array(i)) - 8), LookIn:=xlValues, lookat:=xlPart)
                
                If Not c Is Nothing Then
                    Cells(c.Cells.Cells.Row, c.Cells.Cells.Column).Activate
                    Worksheets("q_recon").Cells(j + 1, 2).Value = balance_begin_label
                    Worksheets("q_recon").Cells(j + 1, 3).Value = ActiveCell.Offset(0, 2).Value
                    Worksheets("q_recon").Cells(j + 1, 4).Value = ActiveCell.Offset(0, 7).Value
                Else
                    Worksheets("q_recon").Cells(j + 1, 2).Value = balance_begin_label
                    Worksheets("q_recon").Cells(j + 1, 3).Value = 0
                    Worksheets("q_recon").Cells(j + 1, 4).Value = 0
                End If
            End With
            
            With ActiveSheet.Columns("A:A")
                Set c = .Find(currency_array(i), LookIn:=xlValues, lookat:=xlPart)
                
                If Not c Is Nothing Then
                    Cells(c.Cells.Cells.Row, c.Cells.Cells.Column).Activate
                    Worksheets("q_recon").Cells(j + 1, 5).Value = ActiveCell.Offset(0, 6).Value - Worksheets("q_recon").Cells(j + 1, 3).Value
                    Worksheets("q_recon").Cells(j + 1, 6).Value = ActiveCell.Offset(0, 11).Value - Worksheets("q_recon").Cells(j + 1, 4).Value
                    Worksheets("q_recon").Cells(j + 1, 7).Value = ActiveCell.Offset(0, 6).Value
                    Worksheets("q_recon").Cells(j + 1, 8).Value = ActiveCell.Offset(0, 11).Value
                Else
                    Worksheets("q_recon").Cells(j + 1, 5).Value = 0
                    Worksheets("q_recon").Cells(j + 1, 6).Value = 0
                    Worksheets("q_recon").Cells(j + 1, 7).Value = 0
                    Worksheets("q_recon").Cells(j + 1, 8).Value = 0
                End If
            End With
            j = j + 1
            
            Range("A1").Activate
            
            'Accumulate opening totals addresses
            Worksheets("q_recon").Activate
            cash_total_beg_addresses = cash_total_beg_addresses + Cells(j, 4).Address + ","
            investments_total_beg_addresses = investments_total_beg_addresses + Cells(j, 6).Address + ","
            portfoliototal_total_beg_addresses = portfoliototal_total_beg_addresses + Cells(j, 8).Address + ","
            
            
            'Scan q_iedl
            Worksheets("q_iedl").Activate
            Range("A1").Activate
            Dim q_iedl_first_find_address As String
            Dim country As String
            Dim total_address As String
                        
            With ActiveSheet.Columns("B:B")
                Set c = .Find(Right(currency_array(i), Len(currency_array(i)) - 8), LookIn:=xlValues, lookat:=xlWhole)
                If Not c Is Nothing Then
                    q_iedl_first_find_address = c.Address
                    Do
                        Cells(c.Cells.Cells.Row, c.Cells.Cells.Column).Activate
                        ActiveCell.Offset(0, 1).Activate

                        Do
                            Selection.End(xlDown).Select
                            Selection.End(xlDown).Select
                            If UCase(Left(ActiveCell.Value, 8)) = "TOTAL - " Then
                                total_address = ActiveCell.Address
                                Range(total_address).Select
                                Selection.End(xlToLeft).Select
                                Selection.End(xlUp).Select
                                country = ActiveCell.Value
                                Range(total_address).Activate
                                If ActiveCell.Offset(0, 4).Value <> 0 Then
                                    Worksheets("q_recon").Cells(j + 1, 2).Value = Right(ActiveCell.Value, Len(ActiveCell.Value) - 8) + " (" + country + ")"
                                    Worksheets("q_recon").Cells(j + 1, 3).Value = ActiveCell.Offset(0, 4).Value
                                    Worksheets("q_recon").Cells(j + 1, 4).Value = ActiveCell.Offset(0, 8).Value
                                    Worksheets("q_recon").Cells(j + 1, 5).Value = 0
                                    Worksheets("q_recon").Cells(j + 1, 6).Value = 0
                                    Worksheets("q_recon").Cells(j + 1, 7).Value = ActiveCell.Offset(0, 4).Value
                                    Worksheets("q_recon").Cells(j + 1, 8).Value = ActiveCell.Offset(0, 8).Value
                                    j = j + 1
                                End If
                                If ActiveCell.Offset(0, 5).Value <> 0 Then
                                    Worksheets("q_recon").Cells(j + 1, 2).Value = Range("H6").Value + " " + Range("H7").Value + " - " + Right(ActiveCell.Value, Len(ActiveCell.Value) - 8) + " (" + country + ")"
                                    Worksheets("q_recon").Cells(j + 1, 3).Value = ActiveCell.Offset(0, 5).Value
                                    Worksheets("q_recon").Cells(j + 1, 4).Value = ActiveCell.Offset(0, 9).Value
                                    Worksheets("q_recon").Cells(j + 1, 5).Value = 0
                                    Worksheets("q_recon").Cells(j + 1, 6).Value = 0
                                    Worksheets("q_recon").Cells(j + 1, 7).Value = ActiveCell.Offset(0, 5).Value
                                    Worksheets("q_recon").Cells(j + 1, 8).Value = ActiveCell.Offset(0, 9).Value
                                    j = j + 1
                                End If
                                
                            End If
                            'MsgBox ActiveCell.Offset(1, -1).Value
                        Loop While UCase(Left(ActiveCell.Offset(1, -1).Value, 8)) <> "TOTAL - "
                        Set c = .FindNext(c)
                    Loop While Not c Is Nothing And q_iedl_first_find_address <> c.Address
                End If
            End With
            
            'Scan q_dpwddl
            Worksheets("q_dpwddl").Activate
            Range("A1").Activate
            Dim q_dpwddl_first_find_address As String
            
            With ActiveSheet.Columns("A:A")
                Set c = .Find(Right(currency_array(i), Len(currency_array(i)) - 8), LookIn:=xlValues, lookat:=xlWhole)
                If Not c Is Nothing Then
                    q_dpwddl_first_find_address = c.Address
                    Do
                        Cells(c.Cells.Cells.Row, c.Cells.Cells.Column).Activate
                        ActiveCell.Offset(0, 1).Activate

                        Do
                            Selection.End(xlDown).Select
                            Selection.End(xlDown).Select
                            If UCase(Left(ActiveCell.Value, 8)) = "TOTAL - " Then
                                Worksheets("q_recon").Cells(j + 1, 2).Value = Right(ActiveCell.Value, Len(ActiveCell.Value) - 8)
                                Worksheets("q_recon").Cells(j + 1, 3).Value = ActiveCell.Offset(0, 3).Value
                                Worksheets("q_recon").Cells(j + 1, 4).Value = ActiveCell.Offset(0, 5).Value
                                Worksheets("q_recon").Cells(j + 1, 5).Value = 0
                                Worksheets("q_recon").Cells(j + 1, 6).Value = 0
                                Worksheets("q_recon").Cells(j + 1, 7).Value = ActiveCell.Offset(0, 3).Value
                                Worksheets("q_recon").Cells(j + 1, 8).Value = ActiveCell.Offset(0, 5).Value
                                j = j + 1
                            End If
                            'MsgBox ActiveCell.Offset(1, -1).Value
                        Loop While UCase(Left(ActiveCell.Offset(1, -1).Value, 8)) <> "TOTAL - "
                        Set c = .FindNext(c)
                    Loop While Not c Is Nothing And q_dpwddl_first_find_address <> c.Address
                End If
            End With
            
            'Scan q_bysldl
            Worksheets("q_bysldl").Activate
            Range("A1").Activate
            Dim q_bysldl_first_find_address As String
            
            With ActiveSheet.Columns("A:A")
                Set c = .Find(Right(currency_array(i), Len(currency_array(i)) - 8), LookIn:=xlValues, lookat:=xlWhole)
                If Not c Is Nothing Then
                    q_bysldl_first_find_address = c.Address
                    Do
                        Cells(c.Cells.Cells.Row, c.Cells.Cells.Column).Activate
                        ActiveCell.Offset(0, 2).Activate

                        Do
                            Selection.End(xlDown).Select
                            Selection.End(xlDown).Select
                            If UCase(Left(ActiveCell.Value, 8)) = "TOTAL - " Then
                                Worksheets("q_recon").Cells(j + 1, 2).Value = Right(ActiveCell.Value, Len(ActiveCell.Value) - 8)
                                Worksheets("q_recon").Cells(j + 1, 3).Value = ActiveCell.Offset(0, 6).Value
                                Worksheets("q_recon").Cells(j + 1, 4).Value = ActiveCell.Offset(0, 11).Value
                                Worksheets("q_recon").Cells(j + 1, 5).Value = ActiveCell.Offset(0, 5).Value
                                Worksheets("q_recon").Cells(j + 1, 6).Value = ActiveCell.Offset(0, 9).Value
                                Worksheets("q_recon").Cells(j + 1, 7).Value = ActiveCell.Offset(0, 7).Value
                                Worksheets("q_recon").Cells(j + 1, 8).Value = ActiveCell.Offset(0, 12).Value
                                j = j + 1
                            End If
                            'MsgBox ActiveCell.Offset(1, -1).Value
                        Loop While UCase(Left(ActiveCell.Offset(2, -2).Value, 8)) <> "TOTAL - "
                        Set c = .FindNext(c)
                    Loop While Not c Is Nothing And q_bysldl_first_find_address <> c.Address
                End If
            End With
            
            'Scan q_rglfdl
            Worksheets("q_rglfdl").Activate
            Range("A1").Activate
            Dim q_rglfdl_first_find_address As String
            
            With ActiveSheet.Columns("A:A")
                Set c = .Find(currency_array(i), LookIn:=xlValues, lookat:=xlWhole)
                If Not c Is Nothing Then
                    q_rglfdl_first_find_address = c.Address
                    Do
                        Cells(c.Cells.Cells.Row, c.Cells.Cells.Column).Activate
                        Worksheets("q_recon").Cells(j + 1, 2).Value = gainloss_label
                        Worksheets("q_recon").Cells(j + 1, 3).Value = 0
                        Worksheets("q_recon").Cells(j + 1, 4).Value = ActiveCell.Offset(0, 4).Value
                        Worksheets("q_recon").Cells(j + 1, 5).Value = 0
                        Worksheets("q_recon").Cells(j + 1, 6).Value = 0
                        Worksheets("q_recon").Cells(j + 1, 7).Value = 0
                        Worksheets("q_recon").Cells(j + 1, 8).Value = ActiveCell.Offset(0, 4).Value
                        j = j + 1
                        Set c = .FindNext(c)
                    Loop While Not c Is Nothing And q_rglfdl_first_find_address <> c.Address
                End If
            End With
            
            'Scan q_pvald2
            Worksheets("q_pvald2").Activate
            With ActiveSheet.Columns("E:E")
                Set c = .Find(Right(currency_array(i), Len(currency_array(i)) - 8), LookIn:=xlValues, lookat:=xlPart)
                'MsgBox (currency_array(i))
                If Not c Is Nothing Then
                    Cells(c.Cells.Cells.Row, c.Cells.Cells.Column).Activate
                    Worksheets("q_recon").Cells(j + 1, 2).Value = balance_end_label
                    Worksheets("q_recon").Cells(j + 1, 3).Value = ActiveCell.Offset(0, 2).Value
                    Worksheets("q_recon").Cells(j + 1, 4).Value = ActiveCell.Offset(0, 7).Value
                Else
                    Worksheets("q_recon").Cells(j + 1, 2).Value = balance_end_label
                    Worksheets("q_recon").Cells(j + 1, 3).Value = 0
                    Worksheets("q_recon").Cells(j + 1, 4).Value = 0
                End If
            End With
            
            With ActiveSheet.Columns("A:A")
                Set c = .Find(currency_array(i), LookIn:=xlValues, lookat:=xlPart)
                
                If Not c Is Nothing Then
                    Cells(c.Cells.Cells.Row, c.Cells.Cells.Column).Activate
                    Worksheets("q_recon").Cells(j + 1, 5).Value = ActiveCell.Offset(0, 6).Value - Worksheets("q_recon").Cells(j + 1, 3).Value
                    Worksheets("q_recon").Cells(j + 1, 6).Value = ActiveCell.Offset(0, 11).Value - Worksheets("q_recon").Cells(j + 1, 4).Value
                    Worksheets("q_recon").Cells(j + 1, 7).Value = ActiveCell.Offset(0, 6).Value
                    Worksheets("q_recon").Cells(j + 1, 8).Value = ActiveCell.Offset(0, 11).Value
                Else
                    Worksheets("q_recon").Cells(j + 1, 5).Value = 0
                    Worksheets("q_recon").Cells(j + 1, 6).Value = 0
                    Worksheets("q_recon").Cells(j + 1, 7).Value = 0
                    Worksheets("q_recon").Cells(j + 1, 8).Value = 0
                End If
            End With
            j = j + 1
            
            Range("A1").Activate
            
            'Add verifcation line after all categories
            Dim range_begin_row As Integer
            Dim range_end_row As Integer
            Dim range_address As String
            
            Worksheets("q_recon").Activate
            
            Cells(j + 1, 3).Select
            
            
            If Selection.Offset(-2, 0).Value = "" Then
                Selection.Offset(-1, 0).Select
                range_begin_row = Selection.Row
                range_end_row = Selection.Row
            Else
                Selection.End(xlUp).Select
                Selection.End(xlUp).Select
                range_begin_row = Selection.Row
                Selection.End(xlDown).Select
                range_end_row = Selection.Row
            End If
            Selection.Offset(1, 0).Select
            ActiveCell.Offset(0, -1).Value = verification_label

            range_address = "$C$" + CStr(range_begin_row) + ":" + "$C$" + CStr(range_end_row - 1)
            Selection.Formula = "=Sum(" + range_address + ") - $C$" + CStr(range_end_row)
            range_address = "$D$" + CStr(range_begin_row) + ":" + "$D$" + CStr(range_end_row - 1)
            Selection.Offset(0, 1).Formula = "=Sum(" + range_address + ") - $D$" + CStr(range_end_row)
            range_address = "$E$" + CStr(range_begin_row) + ":" + "$E$" + CStr(range_end_row - 1)
            Selection.Offset(0, 2).Formula = "=Sum(" + range_address + ") - $E$" + CStr(range_end_row)
            range_address = "$F$" + CStr(range_begin_row) + ":" + "$F$" + CStr(range_end_row - 1)
            Selection.Offset(0, 3).Formula = "=Sum(" + range_address + ") - $F$" + CStr(range_end_row)
            range_address = "$G$" + CStr(range_begin_row) + ":" + "$G$" + CStr(range_end_row - 1)
            Selection.Offset(0, 4).Formula = "=Sum(" + range_address + ") - $G$" + CStr(range_end_row)
            range_address = "$H$" + CStr(range_begin_row) + ":" + "$H$" + CStr(range_end_row - 1)
            Selection.Offset(0, 5).Formula = "=Sum(" + range_address + ") - $H$" + CStr(range_end_row)
            
            cash_total_end_addresses = cash_total_end_addresses + Selection.Offset(-1, 1).Address + ","
            investments_total_end_addresses = investments_total_end_addresses + Selection.Offset(-1, 3).Address + ","
            portfoliototal_total_end_addresses = portfoliototal_total_end_addresses + Selection.Offset(-1, 5).Address + ","
            cash_verification_addresses = cash_verification_addresses + Selection.Offset(0, 1).Address + ","
            investments_verification_addresses = investments_verification_addresses + Selection.Offset(0, 3).Address + ","
            portfoliototal_verification_addresses = portfoliototal_verification_addresses + Selection.Offset(0, 5).Address + ","

            j = j + 1
            
            j = j + 2

        Next
    Worksheets("q_recon").Activate

    Cells(j, 1).Activate
    ActiveCell.Value = grand_total_end_label
    ActiveCell.Offset(0, 3).Formula = "=Sum(" + Left(cash_total_end_addresses, Len(cash_total_end_addresses) - 1) + ")"
    ActiveCell.Offset(0, 5).Formula = "=Sum(" + Left(investments_total_end_addresses, Len(investments_total_end_addresses) - 1) + ")"
    ActiveCell.Offset(0, 7).Formula = "=Sum(" + Left(portfoliototal_total_end_addresses, Len(portfoliototal_total_end_addresses) - 1) + ")"
    Cells(j, 1).Offset(1, 0).Activate
    ActiveCell.Value = verification_label
    ActiveCell.Offset(0, 3).Formula = "=Sum(" + Left(cash_verification_addresses, Len(cash_verification_addresses) - 1) + ")"
    ActiveCell.Offset(0, 5).Formula = "=Sum(" + Left(investments_verification_addresses, Len(investments_verification_addresses) - 1) + ")"
    ActiveCell.Offset(0, 7).Formula = "=Sum(" + Left(portfoliototal_verification_addresses, Len(portfoliototal_verification_addresses) - 1) + ")"
    
    Range("A9").Select
    ActiveCell.Value = grand_total_beg_label
    ActiveCell.Offset(0, 3).Formula = "=Sum(" + Left(cash_total_beg_addresses, Len(cash_total_beg_addresses) - 1) + ")"
    ActiveCell.Offset(0, 5).Formula = "=Sum(" + Left(investments_total_beg_addresses, Len(investments_total_beg_addresses) - 1) + ")"
    ActiveCell.Offset(0, 7).Formula = "=Sum(" + Left(portfoliototal_total_beg_addresses, Len(portfoliototal_total_beg_addresses) - 1) + ")"
    
    Columns("A:A").Select
    Selection.ColumnWidth = 3
    Columns("B:B").Select
    Selection.ColumnWidth = 45
    Columns("C:H").Select
    Selection.ColumnWidth = 12
    Columns("C:H").Select
    Selection.NumberFormat = "#,##0.00"
        
    Range("A1").Value = summary_page_title
    Range("A1:H1").Select
    Selection.Merge
    Selection.HorizontalAlignment = xlCenter
    Range("A2").Value = Worksheets("q_pvald2").Range("A2").Value
    Range("A2:H2").Select
    Selection.Merge
    Selection.HorizontalAlignment = xlCenter
    Range("A3").Value = summary_page_period
    Range("A3:H3").Select
    Selection.Merge
    Selection.HorizontalAlignment = xlCenter
    Range("A4").Value = Worksheets("q_pvald2").Range("A4").Value
    
    Range("C5").Value = cash_label
    Range("C5:D5").Select
    Selection.Merge
    Range("C6").Value = loccur_label1
    Range("C7").Value = loccur_label2
    Range("D6").Value = repcur_label1
    Range("D7").Value = repcur_label2
    Range("E5").Value = asset_label
    Range("E5:F5").Select
    Selection.Merge
    Range("E6").Value = loccur_label1
    Range("E7").Value = loccur_label2
    Range("F6").Value = repcur_label1
    Range("F7").Value = repcur_label2
    Range("G5").Value = total_portfolio_label
    Range("G5:H5").Select
    Selection.Merge
    Range("G6").Value = loccur_label1
    Range("G7").Value = loccur_label2
    Range("H6").Value = repcur_label1
    Range("H7").Value = repcur_label2
    
    
    Range("C5:H7").Select
    Selection.HorizontalAlignment = xlCenter
    
    Cells.Select
    Selection.Font.Size = 8
    
'Add underline formatting on column headers
Range("A4:H4").Select
With Selection.Borders(xlEdgeBottom)
    .LineStyle = xlContinuous
    .Weight = xlThin
    .ColorIndex = xlAutomatic
End With

'Adjust PageSetup Settings
With ActiveSheet.PageSetup
    .LeftMargin = Application.InchesToPoints(0.5)
    .RightMargin = Application.InchesToPoints(0.5)
    .TopMargin = Application.InchesToPoints(0.5)
    .BottomMargin = Application.InchesToPoints(0.5)
    .HeaderMargin = Application.InchesToPoints(0)
    .FooterMargin = Application.InchesToPoints(0)
    .Orientation = xlLandscape
    .PaperSize = xlPaperLetter
    .CenterFooter = "Page &P of &N"
End With

Range("A1").Select

End Sub
Sub FixPageNumbers()
Dim pagecount As Integer

pagecount = CInt(Worksheets("q_recon").HPageBreaks.Count) + 1
MsgBox "q_recon" + CStr(pagecount)
Worksheets("q_pvald1").PageSetup.FirstPageNumber = pagecount + 1
pagecount = pagecount + CInt(Worksheets("q_q_pvald1").HPageBreaks.Count) + 1
MsgBox "q_pvald1" + CStr(pagecount)
Worksheets("q_iedl").FirstPageNumber = pagecount + 1


MsgBox Worksheets("q_pvald1").HPageBreaks.Count

End Sub
Sub q_pvaldl(period As Integer)
Dim dataqueryConn As String
Workbooks("q_acntdl.xls").Worksheets.Add 
ActiveSheet.Name = "q_pvald" + CStr(period)

dataqueryConn = "TEXT;U:\" + Application.UserName + "\Private\Axys\" + ActiveSheet.Name + ".txt"
With ActiveSheet.QueryTables.Add(Connection:=dataqueryConn, Destination:=Range("A1"))
        .Name = ActiveSheet.Name
        .FieldNames = True
        .RowNumbers = False
        .FillAdjacentFormulas = False
        .PreserveFormatting = True
        .RefreshOnFileOpen = False
        .RefreshStyle = xlInsertDeleteCells
        .SavePassword = False
        .SaveData = True
        .AdjustColumnWidth = True
        .RefreshPeriod = 0
        .TextFilePromptOnRefresh = False
        .TextFilePlatform = 1252
        .TextFileStartRow = 1
        .TextFileParseType = xlDelimited
        .TextFileTextQualifier = xlTextQualifierDoubleQuote
        .TextFileConsecutiveDelimiter = False
        .TextFileTabDelimiter = True
        .TextFileSemicolonDelimiter = False
        .TextFileCommaDelimiter = False
        .TextFileSpaceDelimiter = False
        .TextFileColumnDataTypes = Array(1)
        .TextFileTrailingMinusNumbers = True
        .Refresh BackgroundQuery:=False
End With
    
Cells.Select
Selection.Font.Size = 8

'Adjust PageSetup Settings
With ActiveSheet.PageSetup
    .LeftMargin = Application.InchesToPoints(0.5)
    .RightMargin = Application.InchesToPoints(0.5)
    .TopMargin = Application.InchesToPoints(0.5)
    .BottomMargin = Application.InchesToPoints(0.5)
    .HeaderMargin = Application.InchesToPoints(0)
    .FooterMargin = Application.InchesToPoints(0)
    .Orientation = xlLandscape
    .PaperSize = xlPaperLetter
    .CenterFooter = "Page &P of &N"
End With



'Adjust Column widths and formats
Columns("A:C").Select
Selection.ColumnWidth = 0.5

Columns("D:D").Select
Selection.ColumnWidth = 11
Selection.NumberFormat = "#,##0.000"

Columns("E:E").Select
Selection.ColumnWidth = 22.5
Selection.WrapText = True

Columns("F:F").Select
Selection.ColumnWidth = 7
Columns("H:H").Select
Selection.ColumnWidth = 7
Columns("J:J").Select
Selection.ColumnWidth = 6
Selection.NumberFormat = "0.0000"
Columns("K:K").Select
Selection.ColumnWidth = 7
Columns("M:M").Select
Selection.ColumnWidth = 7
Columns("O:O").Select
Selection.ColumnWidth = 5.5
Columns("G:G").Select
Selection.ColumnWidth = 11
Columns("I:I").Select
Selection.ColumnWidth = 11
Columns("L:L").Select
Selection.ColumnWidth = 11
Columns("N:N").Select
Selection.ColumnWidth = 11

Columns("F:I").Select
Selection.NumberFormat = "#,##0.00"
Columns("K:O").Select
Selection.NumberFormat = "#,##0.00"

Range("D6:O7").HorizontalAlignment = xlCenter


'Merge Column headers
Range("A1:O1").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter
Range("A2:O2").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter
Range("A3:O3").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter
Range("F5:I5").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter
Range("K5:O5").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter

'Add underline formatting on column headers
Range("A7:O7").Select
With Selection.Borders(xlEdgeBottom)
    .LineStyle = xlContinuous
    .Weight = xlThin
    .ColorIndex = xlAutomatic
End With

ActiveSheet.PageSetup.PrintTitleRows = "$1:$7"

Range("A1").Activate
End Sub
Sub q_nctrdl()
Workbooks("q_acntdl.xls").Worksheets.Add
ActiveSheet.Name = "q_nctrdl"

Dim dataqueryConn As String
dataqueryConn = "TEXT;U:\" + Application.UserName + "\Private\Axys\" + ActiveSheet.Name + ".txt"
With ActiveSheet.QueryTables.Add(Connection:=dataqueryConn, Destination:=Range("A1"))
        .Name = "q_nctrdl"
        .FieldNames = True
        .RowNumbers = False
        .FillAdjacentFormulas = False
        .PreserveFormatting = True
        .RefreshOnFileOpen = False
        .RefreshStyle = xlInsertDeleteCells
        .SavePassword = False
        .SaveData = True
        .AdjustColumnWidth = True
        .RefreshPeriod = 0
        .TextFilePromptOnRefresh = False
        .TextFilePlatform = 1252
        .TextFileStartRow = 1
        .TextFileParseType = xlDelimited
        .TextFileTextQualifier = xlTextQualifierDoubleQuote
        .TextFileConsecutiveDelimiter = False
        .TextFileTabDelimiter = True
        .TextFileSemicolonDelimiter = False
        .TextFileCommaDelimiter = False
        .TextFileSpaceDelimiter = False
        .TextFileColumnDataTypes = Array(1)
        .TextFileTrailingMinusNumbers = True
        .Refresh BackgroundQuery:=False
End With

Cells.Select
Selection.Font.Size = 8

'Adjust PageSetup Settings
With ActiveSheet.PageSetup
    .LeftMargin = Application.InchesToPoints(0.5)
    .RightMargin = Application.InchesToPoints(0.5)
    .TopMargin = Application.InchesToPoints(0.5)
    .BottomMargin = Application.InchesToPoints(0.5)
    .HeaderMargin = Application.InchesToPoints(0)
    .FooterMargin = Application.InchesToPoints(0)
    .Orientation = xlLandscape
    .PaperSize = xlPaperLetter
    .CenterFooter = "Page &P of &N"
End With

'Adjust Date based on language
If Range("A1").Value = "SOMMAIRE DE TRANSACTION SANS IMPACT SUR L'ENCAISSE" Then
    Columns("D:D").NumberFormat = "dd-mm-yy;@"
    Columns("I:I").NumberFormat = "dd-mm-yy;@"
ElseIf Range("A1").Value = "NON-CASH TRANSACTION SUMMARY" Then
    Columns("D:D").NumberFormat = "mm-dd-yy;@"
    Columns("I:I").NumberFormat = "mm-dd-yy;@"
End If

'Add underline formatting on column headers
Range("A7:L7").Select
With Selection.Borders(xlEdgeBottom)
    .LineStyle = xlContinuous
    .Weight = xlThin
    .ColorIndex = xlAutomatic
End With

'Adjust Column widths and formats
Columns("A:A").Select
Selection.ColumnWidth = 0.5
Columns("B:B").Select
Selection.ColumnWidth = 15
Columns("C:C").Select
Selection.ColumnWidth = 25
Selection.WrapText = True
Columns("D:D").Select
Selection.ColumnWidth = 6.57
Columns("I:I").Select
Selection.ColumnWidth = 6.57
Columns("E:E").Select
Selection.ColumnWidth = 11
Selection.NumberFormat = "#,##0.000"
Columns("F:F").Select
Selection.ColumnWidth = 11
Selection.NumberFormat = "#,##0.00"
Columns("H:H").Select
Selection.ColumnWidth = 11
Selection.NumberFormat = "#,##0.00"
Columns("J:J").Select
Selection.ColumnWidth = 11
Selection.NumberFormat = "#,##0.00"
Columns("L:L").Select
Selection.ColumnWidth = 11
Selection.NumberFormat = "#,##0.00"
Columns("G:G").Select
Selection.ColumnWidth = 6
Selection.NumberFormat = "0.0000"
Columns("K:K").Select
Selection.ColumnWidth = 6
Selection.NumberFormat = "0.0000"

Range("A5:O7").Select
Selection.HorizontalAlignment = xlCenter

'Fix report title
Range("A1:L1").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter
Range("A2:L2").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter
Range("A3:L3").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter

ActiveSheet.PageSetup.PrintTitleRows = "$1:$7"

Range("A1").Activate

End Sub
Sub q_iedl()
Workbooks("q_acntdl.xls").Worksheets.Add
ActiveSheet.Name = "q_iedl"

Dim dataqueryConn As String
dataqueryConn = "TEXT;U:\" + Application.UserName + "\Private\Axys\" + ActiveSheet.Name + ".txt"

With ActiveSheet.QueryTables.Add(Connection:=dataqueryConn, Destination:=Range("A1"))
        .Name = "q_iedl"
        .FieldNames = True
        .RowNumbers = False
        .FillAdjacentFormulas = False
        .PreserveFormatting = True
        .RefreshOnFileOpen = False
        .RefreshStyle = xlInsertDeleteCells
        .SavePassword = False
        .SaveData = True
        .AdjustColumnWidth = True
        .RefreshPeriod = 0
        .TextFilePromptOnRefresh = False
        .TextFilePlatform = 1252
        .TextFileStartRow = 1
        .TextFileParseType = xlDelimited
        .TextFileTextQualifier = xlTextQualifierDoubleQuote
        .TextFileConsecutiveDelimiter = False
        .TextFileTabDelimiter = True
        .TextFileSemicolonDelimiter = False
        .TextFileCommaDelimiter = False
        .TextFileSpaceDelimiter = False
        .TextFileColumnDataTypes = Array(1)
        .TextFileTrailingMinusNumbers = True
        .Refresh BackgroundQuery:=False
End With

Cells.Select
Selection.Font.Size = 8

'Adjust PageSetup Settings
With ActiveSheet.PageSetup
    .LeftMargin = Application.InchesToPoints(0.5)
    .RightMargin = Application.InchesToPoints(0.5)
    .TopMargin = Application.InchesToPoints(0.5)
    .BottomMargin = Application.InchesToPoints(0.5)
    .HeaderMargin = Application.InchesToPoints(0)
    .FooterMargin = Application.InchesToPoints(0)
    .Orientation = xlLandscape
    .PaperSize = xlPaperLetter
    .CenterFooter = "Page &P of &N"
End With

'Adjust Date based on language
Columns("D:E").Select
If Range("A1").Value = "RAPPORT DE REVENUS" Then
    Selection.NumberFormat = "dd-mm-yy;@"
ElseIf Range("A1").Value = "INCOME SUMMARY REPORT" Then
    Selection.NumberFormat = "mm-dd-yy;@"
End If
Columns("D:E").EntireColumn.AutoFit

'Adjust Column widths and formats
Columns("A:C").Select
Selection.ColumnWidth = 1
Columns("F:F").Select
Selection.ColumnWidth = 32
Columns("G:G").Select
Selection.ColumnWidth = 10.5
Columns("H:H").Select
Selection.ColumnWidth = 9
Columns("I:I").Select
Selection.ColumnWidth = 10.5
Columns("J:J").Select
Selection.ColumnWidth = 7
Columns("K:K").Select
Selection.ColumnWidth = 10.5
Columns("L:L").Select
Selection.ColumnWidth = 9
Columns("M:M").Select
Selection.ColumnWidth = 10.5
Columns("F:F").Select
Selection.WrapText = True



Columns("G:I").Select
Selection.NumberFormat = "#,##0.00"
Columns("J:J").Select
Selection.NumberFormat = "0.0000"
Columns("K:M").Select
Selection.NumberFormat = "#,##0.00"


'Insert Rows to Print report title
Range("A1:N1").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter
Range("A2:N2").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter
Range("A3:N3").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter
Range("G5:I5").Select
Selection.Merge
Range("K5:M5").Select
Selection.Merge

Range("A5:M7").HorizontalAlignment = xlCenter

'Add underline formatting on column headers
Range("G5:I5").Select
With Selection.Borders(xlEdgeBottom)
    .LineStyle = xlContinuous
    .Weight = xlThin
    .ColorIndex = xlAutomatic
End With
    
Range("K5:M5").Select
With Selection.Borders(xlEdgeBottom)
    .LineStyle = xlContinuous
    .Weight = xlThin
    .ColorIndex = xlAutomatic
End With
Range("D7:N7").Select
With Selection.Borders(xlEdgeBottom)
    .LineStyle = xlContinuous
    .Weight = xlThin
    .ColorIndex = xlAutomatic
End With
    
ActiveSheet.PageSetup.PrintTitleRows = "$1:$7"

Dim i As Integer
Dim country_check As Boolean
Dim currency_check As Boolean
Dim category_check As Boolean

i = 10

Do While Cells(i, 1).Value <> ""
    
    If Cells(i, 1).Value = Cells(i + 1, 1).Value Then country_check = True Else country_check = False
    If Cells(i, 2).Value = Cells(i + 1, 2).Value Then currency_check = True Else currency_check = False
    If Cells(i, 3).Value = Cells(i + 1, 3).Value Then category_check = True Else category_check = False
    Cells(i, 14).Value = country_check
    Cells(i, 15).Value = currency_check
    Cells(i, 16).Value = category_check
    'If i = 10 Then
    '    Rows("10:12").Select
    '    Selection.Insert Shift:=xlDown
    'End If
    i = i + 1
Loop



Range("A1").Activate
End Sub

Sub q_iedl_ann3()

Workbooks("q_acntdl.xls").Worksheets.Add
ActiveSheet.Name = "q_iedl_ann3"

i = 8

j = 1

blankCnt = 0
dividendCnt = 0
country_text = ""
currency_text = ""
category_text = ""

Do While blankCnt < 10
    If Worksheets("q_iedl").Cells(i, 4).Value = "" Then
        blankCnt = blankCnt + 1
    Else
        blankCnt = 0
        If Worksheets("q_iedl").Cells(i - 1, 4).Value = "" And _
            Worksheets("q_iedl").Cells(i - 3, 1).Value <> "" Then
            country_text = Worksheets("q_iedl").Cells(i - 3, 1).Value
        End If
        If Worksheets("q_iedl").Cells(i - 1, 4).Value = "" And _
            Worksheets("q_iedl").Cells(i - 2, 2).Value <> "" Then
            currency_text = Worksheets("q_iedl").Cells(i - 2, 2).Value
        End If
        If Worksheets("q_iedl").Cells(i - 1, 4).Value = "" And _
            Worksheets("q_iedl").Cells(i - 1, 3).Value <> "" Then
            category_text = Worksheets("q_iedl").Cells(i - 1, 3).Value
        End If
    
        ' If its a dividend
        If InStr(category_text, "ividend") > 0 Then
        
            ' From Canada
            If country_text = "Canada" Then
            
                dividendCnt = dividendCnt + 1
                Worksheets("q_iedl_ann3").Cells(j, 1).Value = "FDDIV.SLIPA[" & dividendCnt & "].TtadivA1"
                Worksheets("q_iedl_ann3").Cells(j, 2).Value = Worksheets("q_iedl").Cells(i, 6).Value
                j = j + 1
                
                'Worksheets("q_iedl_ann3").Cells(j, 1).Value = "FDDIV.SLIPA[" & dividendCnt & "].TtadivA2"
                'If country_text <> "Canada" Then
                '    Worksheets("q_iedl_ann3").Cells(j, 2).Value = "X"
                'End If
                'j = j + 1
                
                Worksheets("q_iedl_ann3").Cells(j, 1).Value = "FDDIV.SLIPA[" & dividendCnt & "].TtadivA7"
                Worksheets("q_iedl_ann3").Cells(j, 2).Value = Worksheets("q_iedl").Cells(i, 11).Value
                j = j + 1
                
                Worksheets("q_iedl_ann3").Cells(j, 1).Value = "FDDIV.SLIPA[" & dividendCnt & "].TtadivA11"
                Worksheets("q_iedl_ann3").Cells(j, 2).Value = Worksheets("q_iedl").Cells(i, 11).Value
                j = j + 1
                
                Worksheets("q_iedl_ann3").Cells(j, 1).Value = "FDDIV.SLIPA[" & dividendCnt & "].TtadivA12"
                Worksheets("q_iedl_ann3").Cells(j, 2).Value = 1
                j = j + 1
            End If
        Else
        
            Do
                i = i + 1
            Loop Until Worksheets("q_iedl").Cells(i, 4).Value = ""
        
        End If
    End If
    
    i = i + 1
Loop

Worksheets("q_iedl_ann3").Cells(1, 1).Activate

ActiveCell.EntireRow.Insert

Worksheets("q_iedl_ann3").Cells(1, 1).Value = "[|0|1]"


End Sub

Sub q_bysldl()
Workbooks("q_acntdl.xls").Worksheets.Add
ActiveSheet.Name = "q_bysldl"

Dim dataqueryConn As String
dataqueryConn = "TEXT;U:\" + Application.UserName + "\Private\Axys\" + ActiveSheet.Name + ".txt"

With ActiveSheet.QueryTables.Add(Connection:=dataqueryConn, Destination:=Range("A1"))
        .Name = "q_bysldl"
        .FieldNames = True
        .RowNumbers = False
        .FillAdjacentFormulas = False
        .PreserveFormatting = True
        .RefreshOnFileOpen = False
        .RefreshStyle = xlInsertDeleteCells
        .SavePassword = False
        .SaveData = True
        .AdjustColumnWidth = True
        .RefreshPeriod = 0
        .TextFilePromptOnRefresh = False
        .TextFilePlatform = 1252
        .TextFileStartRow = 1
        .TextFileParseType = xlDelimited
        .TextFileTextQualifier = xlTextQualifierDoubleQuote
        .TextFileConsecutiveDelimiter = False
        .TextFileTabDelimiter = True
        .TextFileSemicolonDelimiter = False
        .TextFileCommaDelimiter = False
        .TextFileSpaceDelimiter = False
        .TextFileColumnDataTypes = Array(1)
        .TextFileTrailingMinusNumbers = True
        .Refresh BackgroundQuery:=False
End With

Cells.Select
Selection.Font.Size = 8

'Adjust PageSetup Settings
With ActiveSheet.PageSetup
    .LeftMargin = Application.InchesToPoints(0.5)
    .RightMargin = Application.InchesToPoints(0.5)
    .TopMargin = Application.InchesToPoints(0.5)
    .BottomMargin = Application.InchesToPoints(0.5)
    .HeaderMargin = Application.InchesToPoints(0)
    .FooterMargin = Application.InchesToPoints(0)
    .Orientation = xlLandscape
    .PaperSize = xlPaperLetter
    .CenterFooter = "Page &P of &N"
End With



'Adjust Date based on language
'added legend based on accountant request 2015-11-30 FC
Columns("D:E").Select
If Range("A1").Value = "SOMMAIRE DE TRANSACTION SUR LE COMPTE CAPITAL - TRANSACTION RÉGLÉES" Then
    Selection.NumberFormat = "dd-mm-yy;@"
    Range("P1").Value = "Légende"
    Range("P2").Value = "1-ESPECES ET LIQUIDITÉS"
    Range("P3").Value = "15-REVENU FIXE - CANADIEN"
    Range("P4").Value = "20-REVENU FIXE - AMÉRICAIN"
    Range("P5").Value = "25-REVENU FIXE - INTERNATIONAL"
    Range("P6").Value = "30-ACTIONS - CANADIENNES"
    Range("P7").Value = "35-ACTIONS - AMÉRICAINES"
    Range("P8").Value = "40-ACTIONS - INTERNATIONALES"
ElseIf Range("A1").Value = "CAPITAL TRANSACTION SUMMARY - SETTLED TRADES" Then
    Selection.NumberFormat = "mm-dd-yy;@"
    Range("P1").Value = "Legend"
    Range("P2").Value = "1-CASH & EQUIVALENTS"
    Range("P3").Value = "15-FIXED INCOME - CANADIAN"
    Range("P4").Value = "20-FIXED INCOME - U.S."
    Range("P5").Value = "25-FIXED INCOME - INT'L"
    Range("P6").Value = "30-EQUITIES - CANADIAN"
    Range("P7").Value = "35-EQUITIES - U.S."
    Range("P8").Value = "40-EQUITIES - INT'L"
End If




'Add underline formatting on column headers
Range("A7:O7").Select
With Selection.Borders(xlEdgeBottom)
    .LineStyle = xlContinuous
    .Weight = xlThin
    .ColorIndex = xlAutomatic
End With

'Adjust Column widths and formats
Columns("A:C").Select
Selection.ColumnWidth = 0.5
Columns("D:E").Select
Selection.ColumnWidth = 6.57
Columns("F:F").Select
Selection.ColumnWidth = 10
Selection.NumberFormat = "#,##0.000"
Columns("G:G").Select
Selection.ColumnWidth = 25
Selection.WrapText = True
Columns("H:I").Select
Selection.ColumnWidth = 10
Selection.NumberFormat = "#,##0.00"
Columns("J:J").Select
Selection.ColumnWidth = 9
Selection.NumberFormat = "#,##0.00"
Columns("K:K").Select
Selection.ColumnWidth = 6
Selection.NumberFormat = "0.0000"
Columns("L:L").Select
Selection.ColumnWidth = 10
Selection.NumberFormat = "#,##0.00"
Columns("M:M").Select
Selection.ColumnWidth = 6
Selection.NumberFormat = "0.0000"
Columns("N:N").Select
Selection.ColumnWidth = 10
Selection.NumberFormat = "#,##0.00"
Columns("O:O").Select
Selection.ColumnWidth = 9
Selection.NumberFormat = "#,##0.00"

Range("A5:O7").Select
Selection.HorizontalAlignment = xlCenter

'Fix report title
Range("A1:O1").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter
Range("A2:O2").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter
Range("A3:O3").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter

ActiveSheet.PageSetup.PrintTitleRows = "$1:$7"

Range("A1").Activate

End Sub
Sub q_dpwddl()
Workbooks("q_acntdl.xls").Worksheets.Add
ActiveSheet.Name = "q_dpwddl"

Dim dataqueryConn As String
dataqueryConn = "TEXT;U:\" + Application.UserName + "\Private\Axys\" + ActiveSheet.Name + ".txt"

With ActiveSheet.QueryTables.Add(Connection:=dataqueryConn, Destination:=Range("A1"))
        .Name = "q_dpwddl"
        .FieldNames = True
        .RowNumbers = False
        .FillAdjacentFormulas = False
        .PreserveFormatting = True
        .RefreshOnFileOpen = False
        .RefreshStyle = xlInsertDeleteCells
        .SavePassword = False
        .SaveData = True
        .AdjustColumnWidth = True
        .RefreshPeriod = 0
        .TextFilePromptOnRefresh = False
        .TextFilePlatform = 1252
        .TextFileStartRow = 1
        .TextFileParseType = xlDelimited
        .TextFileTextQualifier = xlTextQualifierDoubleQuote
        .TextFileConsecutiveDelimiter = False
        .TextFileTabDelimiter = True
        .TextFileSemicolonDelimiter = False
        .TextFileCommaDelimiter = False
        .TextFileSpaceDelimiter = False
        .TextFileColumnDataTypes = Array(1)
        .TextFileTrailingMinusNumbers = True
        .Refresh BackgroundQuery:=False
End With

Cells.Select
Selection.Font.Size = 8

'Adjust PageSetup Settings
With ActiveSheet.PageSetup
    .LeftMargin = Application.InchesToPoints(0.5)
    .RightMargin = Application.InchesToPoints(0.5)
    .TopMargin = Application.InchesToPoints(0.5)
    .BottomMargin = Application.InchesToPoints(0.5)
    .HeaderMargin = Application.InchesToPoints(0)
    .FooterMargin = Application.InchesToPoints(0)
    .Orientation = xlPortrait
    .PaperSize = xlPaperLetter
    .CenterFooter = "Page &P of &N"
End With

'Adjust Date based on language
Columns("C:C").Select
If Range("A1").Value = "Dépôts, retraits et frais " Then
    Selection.NumberFormat = "dd-mm-yy;@"
ElseIf Range("A1").Value = "DEPOSIT, WITHDRAWALS, AND FEES" Then
    Selection.NumberFormat = "mm-dd-yy;@"
End If


'Add underline formatting on column headers
Range("A6:G6").Select
With Selection.Borders(xlEdgeBottom)
    .LineStyle = xlContinuous
    .Weight = xlThin
    .ColorIndex = xlAutomatic
End With

'Adjust Column widths and formats
Columns("A:A").Select
Selection.ColumnWidth = 2
Columns("B:B").Select
Selection.ColumnWidth = 2
Columns("C:C").Select
Selection.ColumnWidth = 7
Columns("D:D").Select
Selection.ColumnWidth = 50
Selection.WrapText = True
Columns("E:E").Select
Selection.NumberFormat = "#,##0.00"
Selection.ColumnWidth = 11
Columns("F:F").Select
Selection.ColumnWidth = 6
Selection.NumberFormat = "0.0000"
Columns("G:G").Select
Selection.ColumnWidth = 11
Selection.NumberFormat = "#,##0.00"

Range("A5:G6").Select
Selection.HorizontalAlignment = xlCenter

'Fix report title
Range("A1:G1").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter
Range("A2:G2").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter
Range("A3:G3").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter

ActiveSheet.PageSetup.PrintTitleRows = "$1:$7"

Range("A8").Select

Range(Selection, Selection.End(xlToRight)).Select
Range(Selection, Selection.End(xlDown)).Select
Selection.Sort Key1:=Range("A8"), Order1:=xlAscending, _
                Key2:=Range("B8"), Order2:=xlAscending, _
                Key3:=Range("C8"), Order3:=xlAscending, _
                Header:=xlGuess, OrderCustom:=1, MatchCase:=False, Orientation:=xlTopToBottom, _
                DataOption1:=xlSortNormal, DataOption2:=xlSortNormal, DataOption3:=xlSortNormal

Range("A8").Select

Rows("8:9").Select
Selection.Insert Shift:=xlDown

Range("A8").Value = ActiveCell.Offset(2, 0).Value
Range("B9").Value = ActiveCell.Offset(2, 1).Value

Range("A10").Select

'Declare variables to store currency and accounts for each row as we loop
Dim currency_str As String
Dim currency_total_str_local As String
Dim currency_total_str_repcur As String
Dim grand_total_str_repcur As String
Dim account_str As String
Dim next_currency_account_case As Integer

'Loop through each row in the report adding subtotals where appropriate
'Loop while the next next row is not blank
Do While ActiveCell.Value <> ""
        
   'Grab the currency and account values for the current row
    currency_str = ActiveCell.Value
    account_str = ActiveCell.Offset(0, 1).Value
    ActiveCell.Value = ""
    ActiveCell.Offset(0, 1).Value = ""
 
    'Figure out if the next row requires sub-totals or not
    'Case when next currency is equal and next account is equal
    If currency_str = ActiveCell.Offset(1, 0).Value And account_str = ActiveCell.Offset(1, 1).Value Then next_currency_account_case = 1
    'Case when next currency is equal and next account is unequal
    If currency_str = ActiveCell.Offset(1, 0).Value And account_str <> ActiveCell.Offset(1, 1).Value Then next_currency_account_case = 2
'chao___f 01/29/2016 : When it's different currency, we move to different currency regardless of the types of transactions.  Otherwise several currencies might be grouped together.
'    'Case when next currency is unequal and next account is unequal
'    If currency_str <> ActiveCell.Offset(1, 0).Value And account_str <> ActiveCell.Offset(1, 1).Value Then next_currency_account_case = 3
    'Case when next currency is unequal
    If currency_str <> ActiveCell.Offset(1, 0).Value Then next_currency_account_case = 3
    
    'Advance to next row
    ActiveCell.Offset(1, 0).Activate
    
    'Select from the 3 different possible cases
    Select Case next_currency_account_case
        'Case when next currency is equal and next account is equal
        Case 1
            X = 1
        
        'Case when next currency is equal and next account is unequal
        Case 2
            Rows(CStr(ActiveCell.Row) + ":" + CStr(ActiveCell.Row + 2)).Select
            Selection.Insert Shift:=xlDown
        
            ActiveCell.Offset(0, 1).Value = "Total - " + account_str

            ActiveCell.Offset(0, 4).Select
            If Selection.Offset(-2, 0).Value = "" Then
                Selection.Offset(-1, 0).Select
                range_begin_row = Selection.Row
                range_end_row = Selection.Row
            Else
                Selection.End(xlUp).Select
                Selection.End(xlUp).Select
                range_begin_row = Selection.Row
                Selection.End(xlDown).Select
                range_end_row = Selection.Row
            End If
            Selection.Offset(1, 0).Select
            currency_total_str_local = currency_total_str_local + "$E$" + CStr(Selection.Row) + ","
            currency_total_str_repcur = currency_total_str_repcur + "$G$" + CStr(Selection.Row) + "+"
            
            range_address = "$E$" + CStr(range_begin_row) + ":" + "$E$" + CStr(range_end_row)
            Selection.Formula = "=Sum(" + range_address + ")"
            range_address = "$G$" + CStr(range_begin_row) + ":" + "$G$" + CStr(range_end_row)
            Selection.Offset(0, 2).Formula = "=Sum(" + range_address + ")"
            Selection.Offset(2, -4).Activate

            ActiveCell.Offset(0, 1).Value = ActiveCell.Offset(1, 1).Value
            ActiveCell.Offset(1, 0).Activate
                        
        'Case when next currency is unequal and next account is unequal
        Case 3
            Rows(CStr(ActiveCell.Row) + ":" + CStr(ActiveCell.Row + 4)).Select
            Selection.Insert Shift:=xlDown
        
            ActiveCell.Offset(0, 1).Value = "Total - " + account_str
            ActiveCell.Offset(0, 4).Select
            
            If Selection.Offset(-2, 0).Value = "" Then
                Selection.Offset(-1, 0).Select
                range_begin_row = Selection.Row
                range_end_row = Selection.Row
            Else
                Selection.End(xlUp).Select
                Selection.End(xlUp).Select
                range_begin_row = Selection.Row
                Selection.End(xlDown).Select
                range_end_row = Selection.Row
            End If
            Selection.Offset(1, 0).Select
            
            currency_total_str_local = currency_total_str_local + "$E$" + CStr(Selection.Row)
            currency_total_str_repcur = currency_total_str_repcur + "$G$" + CStr(Selection.Row)
            
            range_address = "$E$" + CStr(range_begin_row) + ":" + "$E$" + CStr(range_end_row)
            Selection.Formula = "=Sum(" + range_address + ")"
            range_address = "$G$" + CStr(range_begin_row) + ":" + "$G$" + CStr(range_end_row)
            Selection.Offset(0, 2).Formula = "=Sum(" + range_address + ")"
            Selection.Offset(1, -4).Activate
            ActiveCell.Value = "Total - " + currency_str
                        
            ActiveCell.Offset(0, 4).Formula = "=sum(" + currency_total_str_local + ")"
            ActiveCell.Offset(0, 6).Formula = "=sum(" + currency_total_str_repcur + ")"
            grand_total_str_repcur = grand_total_str_repcur + currency_total_str_repcur + "+"
            currency_total_str_local = ""
            currency_total_str_repcur = ""
            ActiveCell.Offset(2, 0).Activate
           
            ActiveCell.Value = ActiveCell.Offset(2, 0).Value
            ActiveCell.Offset(1, 1).Value = ActiveCell.Offset(2, 1).Value
            ActiveCell.Offset(2, 0).Activate
             
    End Select
    
    If ActiveCell.Value = "" Then
        ActiveCell.Offset(-2, 0).Activate
        ActiveCell.Value = "Grand Total"
        ActiveCell.Offset(0, 6).Formula = "=+" + Left(grand_total_str_repcur, Len(grand_total_str_repcur) - 1)
        ActiveCell.Offset(1, 0).Activate
    End If
Loop

Range("A1").Activate

End Sub
Sub q_rglfdl()
Workbooks("q_acntdl.xls").Worksheets.Add
ActiveSheet.Name = "q_rglfdl"

Dim dataqueryConn As String
dataqueryConn = "TEXT;U:\" + Application.UserName + "\Private\Axys\" + ActiveSheet.Name + ".txt"

With ActiveSheet.QueryTables.Add(Connection:=dataqueryConn, Destination:=Range("A1"))
        .Name = "q_rglfdl"
        .FieldNames = True
        .RowNumbers = False
        .FillAdjacentFormulas = False
        .PreserveFormatting = True
        .RefreshOnFileOpen = False
        .RefreshStyle = xlInsertDeleteCells
        .SavePassword = False
        .SaveData = True
        .AdjustColumnWidth = True
        .RefreshPeriod = 0
        .TextFilePromptOnRefresh = False
        .TextFilePlatform = 1252
        .TextFileStartRow = 1
        .TextFileParseType = xlDelimited
        .TextFileTextQualifier = xlTextQualifierDoubleQuote
        .TextFileConsecutiveDelimiter = False
        .TextFileTabDelimiter = True
        .TextFileSemicolonDelimiter = False
        .TextFileCommaDelimiter = False
        .TextFileSpaceDelimiter = False
        .TextFileColumnDataTypes = Array(1)
        .TextFileTrailingMinusNumbers = True
        .Refresh BackgroundQuery:=False
End With

'Adjust PageSetup Settings
With ActiveSheet.PageSetup
    .LeftMargin = Application.InchesToPoints(2)
    .RightMargin = Application.InchesToPoints(0.5)
    .TopMargin = Application.InchesToPoints(0.5)
    .BottomMargin = Application.InchesToPoints(0.5)
    .HeaderMargin = Application.InchesToPoints(0)
    .FooterMargin = Application.InchesToPoints(0)
    .Orientation = xlPortrait
    .PaperSize = xlPaperLetter
    .CenterFooter = "Page &P of &N"
    .PrintTitleRows = "$1:$7"
End With

Cells.Select
Selection.Font.Size = 8

'Adjust Date based on language
Columns("B:B").Select
If Range("A1").Value = "GAINS ET PERTES RÉALISÉS SUR TAUX DE CHANGE" Then
    Selection.NumberFormat = "dd-mm-yy;@"
ElseIf Range("A1").Value = "REALIZED GAINS AND LOSSES ON FOREIGN EXCHANGE" Then
    Selection.NumberFormat = "mm-dd-yy;@"
End If

'Adjust Column widths and formats
Columns("A:A").Select
Selection.ColumnWidth = 10
Columns("B:B").Select
Selection.ColumnWidth = 10
Columns("C:C").Select
Selection.ColumnWidth = 12
Columns("D:D").Select
Selection.ColumnWidth = 12
Columns("E:E").Select
Selection.ColumnWidth = 12
Columns("C:E").Select
Selection.NumberFormat = "#,##0.00"

'Fix report title
Range("A1:E1").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter
Range("A2:E2").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter
Range("A3:E3").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter

Range("A6:E7").HorizontalAlignment = xlCenter

'Add underline formatting on column headers
Range("A7:E7").Select
With Selection.Borders(xlEdgeBottom)
    .LineStyle = xlContinuous
    .Weight = xlThin
    .ColorIndex = xlAutomatic
End With

Range("A9").Select

Range(Selection, Selection.End(xlToRight)).Select
Range(Selection, Selection.End(xlDown)).Select
Selection.Sort Key1:=Range("A9"), Order1:=xlAscending, _
                Key2:=Range("B9"), Order2:=xlAscending, _
                Header:=xlGuess, OrderCustom:=1, MatchCase:=False, Orientation:=xlTopToBottom, _
                DataOption1:=xlSortNormal, DataOption2:=xlSortNormal


Dim currency_str As String
Dim range_begin_row As Integer
Dim range_end_row As Integer
Dim range_address As String
Dim currency_totals_cost As String
Dim currency_totals_str_proceeds As String
Dim currency_totals_str_gainloss As String

Rows("9:9").Select
Selection.Insert Shift:=xlDown

Range("A9").Value = ActiveCell.Offset(1, 0).Value

Range("A10").Activate

Do While ActiveCell.Value <> ""
    currency_str = ActiveCell.Value
    ActiveCell.Value = ""
    
    If currency_str = ActiveCell.Offset(1, 0).Value Then
        ActiveCell.Offset(1, 0).Activate
    Else
        ActiveCell.Offset(1, 0).Activate
        Rows(CStr(ActiveCell.Row) + ":" + CStr(ActiveCell.Row + 2)).Select
        Selection.Insert Shift:=xlDown
        ActiveCell.Value = "Total - " + currency_str
        
        ActiveCell.Offset(0, 2).Select
            
        If Selection.Offset(-2, 0).Value = "" Then
            Selection.Offset(-1, 0).Select
            range_begin_row = Selection.Row
            range_end_row = Selection.Row
        Else
            Selection.End(xlUp).Select
            Selection.End(xlUp).Select
            range_begin_row = Selection.Row
            Selection.End(xlDown).Select
            range_end_row = Selection.Row
        End If
        Selection.Offset(1, 0).Select
        currency_totals_str_cost = currency_totals_str_cost + "$C$" + CStr(Selection.Row) + ","
        currency_totals_str_proceeds = currency_totals_str_proceeds + "$D$" + CStr(Selection.Row) + ","
        currency_totals_str_gainloss = currency_totals_str_gainloss + "$E$" + CStr(Selection.Row) + ","
            
        range_address = "$C$" + CStr(range_begin_row) + ":" + "$C$" + CStr(range_end_row)
        Selection.Formula = "=Sum(" + range_address + ")"
        range_address = "$D$" + CStr(range_begin_row) + ":" + "$D$" + CStr(range_end_row)
        Selection.Offset(0, 1).Formula = "=Sum(" + range_address + ")"
        range_address = "$E$" + CStr(range_begin_row) + ":" + "$E$" + CStr(range_end_row)
        Selection.Offset(0, 2).Formula = "=Sum(" + range_address + ")"
        Selection.Offset(2, -2).Activate
        ActiveCell.Value = ActiveCell.Offset(1, 0).Value
        ActiveCell.Offset(1, 0).Activate
    End If
    
Loop

ActiveCell.Offset(-1, 0).Activate

If ActiveCell.Address <> "$A$9" Then
    ActiveCell.Value = "Grand Total"
    ActiveCell.Offset(0, 2).Formula = "=sum(" + Left(currency_totals_str_cost, Len(currency_totals_str_cost) - 1) + ")"
    ActiveCell.Offset(0, 3).Formula = "=sum(" + Left(currency_totals_str_proceeds, Len(currency_totals_str_proceeds) - 1) + ")"
    ActiveCell.Offset(0, 4).Formula = "=sum(" + Left(currency_totals_str_gainloss, Len(currency_totals_str_gainloss) - 1) + ")"
End If

Range("A1").Activate

End Sub
Sub q_rglsdl()

Workbooks("q_acntdl.xls").Worksheets.Add
ActiveSheet.Name = "q_rglsdl"

Dim dataqueryConn As String
dataqueryConn = "TEXT;U:\" + Application.UserName + "\Private\Axys\" + ActiveSheet.Name + ".txt"

With ActiveSheet.QueryTables.Add(Connection:=dataqueryConn, Destination:=Range("A1"))
        .Name = "q_rglsdl"
        .FieldNames = True
        .RowNumbers = False
        .FillAdjacentFormulas = False
        .PreserveFormatting = True
        .RefreshOnFileOpen = False
        .RefreshStyle = xlInsertDeleteCells
        .SavePassword = False
        .SaveData = True
        .AdjustColumnWidth = True
        .RefreshPeriod = 0
        .TextFilePromptOnRefresh = False
        .TextFilePlatform = 1252
        .TextFileStartRow = 1
        .TextFileParseType = xlDelimited
        .TextFileTextQualifier = xlTextQualifierDoubleQuote
        .TextFileConsecutiveDelimiter = False
        .TextFileTabDelimiter = True
        .TextFileSemicolonDelimiter = False
        .TextFileCommaDelimiter = False
        .TextFileSpaceDelimiter = False
        .TextFileColumnDataTypes = Array(1)
        .TextFileTrailingMinusNumbers = True
        .Refresh BackgroundQuery:=False
End With

'Adjust PageSetup Settings
With ActiveSheet.PageSetup
    .LeftMargin = Application.InchesToPoints(0.5)
    .RightMargin = Application.InchesToPoints(0.5)
    .TopMargin = Application.InchesToPoints(0.5)
    .BottomMargin = Application.InchesToPoints(0.5)
    .HeaderMargin = Application.InchesToPoints(0)
    .FooterMargin = Application.InchesToPoints(0)
    .Orientation = xlPortrait
    .PaperSize = xlPaperLetter
    .CenterFooter = "Page &P of &N"
    .PrintTitleRows = "$1:$7"
End With

Cells.Select
Selection.Font.Size = 8

'Adjust Date based on language
Columns("B:B").Select
If Range("A1").Value = "GAINS ET PERTES RÉALISÉS - TRANSACTIONS RÉGLÉES" Then
    Selection.NumberFormat = "dd-mm-yy;@"
ElseIf Range("A1").Value = "REALIZED GAINS AND LOSSES - SETTLED TRADES" Then
    Selection.NumberFormat = "mm-dd-yy;@"
End If

'Adjust Column widths and formats
Columns("A:A").Select
Selection.ColumnWidth = 1
Columns("B:B").Select
Selection.ColumnWidth = 7
Columns("C:C").Select
Selection.ColumnWidth = 8
Columns("D:D").Select
Selection.ColumnWidth = 22
Selection.WrapText = True
Columns("E:F").Select
Selection.ColumnWidth = 10
Columns("G:I").Select
Selection.ColumnWidth = 9
Columns("J:J").Select
Selection.ColumnWidth = 5

Columns("C:C").Select
Selection.NumberFormat = "#,##0.000"
Columns("E:I").Select
Selection.NumberFormat = "#,##0.00"

'Fix report title
Range("A1:J1").Select
'Range("A1:I1").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter
'Range("A2:I2").Select
Range("A2:J2").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter
'Range("A3:I3").Select
Range("A3:J3").Select
Selection.Merge
Selection.HorizontalAlignment = xlCenter

'Range("A6:I7").HorizontalAlignment = xlCenter
Range("A6:J7").HorizontalAlignment = xlCenter

'Add underline formatting on column headers
'Range("A7:I7").Select
Range("A7:J7").Select
With Selection.Borders(xlEdgeBottom)
    .LineStyle = xlContinuous
    .Weight = xlThin
    .ColorIndex = xlAutomatic
End With
    
'Range("A65536").Select
'Selection.End(xlUp).Select
'Range(Selection, Selection.Offset(0, 8).Address).Select
'Selection.Merge
'
'With Selection
'    .HorizontalAlignment = xlGeneral
'    .VerticalAlignment = xlBottom
'    .WrapText = True
'    .Orientation = 0
'    .AddIndent = False
'    .IndentLevel = 0
'    .ShrinkToFit = False
'    .ReadingOrder = xlContext
'    .MergeCells = True
'End With
'ActiveCell.RowHeight = 50

Range("A1").Activate
    
End Sub
Sub q_rglsdl_ann6()

Workbooks("q_acntdl.xls").Worksheets.Add
ActiveSheet.Name = "q_rglsdl_ann6"

i = 8
j = 1

blankCnt = 0
stockCnt = 0
bondCnt = 0
sector_text = ""
foreign_text = ""

Do While blankCnt < 10
    If Worksheets("q_rglsdl").Cells(i, 2).Value = "" Then
        blankCnt = blankCnt + 1
    Else
        blankCnt = 0
        If Worksheets("q_rglsdl").Cells(i - 1, 2).Value = "" And _
            Worksheets("q_rglsdl").Cells(i - 1, 1).Value <> "" Then
            sector_text = Worksheets("q_rglsdl").Cells(i - 1, 1).Value
            If InStr(sector_text, "CANAD") Then
                foreign_text = ""
            Else
                foreign_text = "X"
            End If
        End If
    
        If Worksheets("q_rglsdl").Cells(i, 4).Value Like "* Due ##-##-##" Then
            
            bondCnt = bondCnt + 1
            
            Worksheets("q_rglsdl_ann6").Cells(j, 1).Value = "FDCAP.SLIPC[" & bondCnt & "].TtwcapC1"
            Worksheets("q_rglsdl_ann6").Cells(j, 2).Value = Worksheets("q_rglsdl").Cells(i, 3).Value
            j = j + 1
        
            Worksheets("q_rglsdl_ann6").Cells(j, 1).Value = "FDCAP.SLIPC[" & bondCnt & "].TtwcapC2"
            Worksheets("q_rglsdl_ann6").Cells(j, 2).Value = Right(Worksheets("q_rglsdl").Cells(i, 4).Value, 8)
            Worksheets("q_rglsdl_ann6").Cells(j, 2).NumberFormat = "YYYY-MM-DD"
            j = j + 1
        
            Worksheets("q_rglsdl_ann6").Cells(j, 1).Value = "FDCAP.SLIPC[" & bondCnt & "].TtwcapC3"
            Worksheets("q_rglsdl_ann6").Cells(j, 2).Value = Left(Worksheets("q_rglsdl").Cells(i, 4).Value, Len(Worksheets("q_rglsdl").Cells(i, 4).Value) - 13)
            j = j + 1
            
            'Worksheets("q_rglsdl_ann6").Cells(j, 1).Value = "FDCAP.SLIPC[" & bondCnt & "].TtwcapC4"
            'j = j + 1
            
            Worksheets("q_rglsdl_ann6").Cells(j, 1).Value = "FDCAP.SLIPC[" & bondCnt & "].TtwcapC5"
            Worksheets("q_rglsdl_ann6").Cells(j, 2).Value = Worksheets("q_rglsdl").Cells(i, 6).Value
            j = j + 1
            
            Worksheets("q_rglsdl_ann6").Cells(j, 1).Value = "FDCAP.SLIPC[" & bondCnt & "].TtwcapC6"
            Worksheets("q_rglsdl_ann6").Cells(j, 2).Value = Worksheets("q_rglsdl").Cells(i, 5).Value
            j = j + 1
            
            'Worksheets("q_rglsdl_ann6").Cells(j, 1).Value = "FDCAP.SLIPC[" & bondCnt & "].TtwcapC7"
            'j = j + 1
            
            Worksheets("q_rglsdl_ann6").Cells(j, 1).Value = "FDCAP.SLIPC[" & bondCnt & "].TtwcapC9"
            Worksheets("q_rglsdl_ann6").Cells(j, 2).Value = foreign_text
            j = j + 1
        Else
            
            stockCnt = stockCnt + 1
            
            Worksheets("q_rglsdl_ann6").Cells(j, 1).Value = "FDCAP.SLIPA[" & stockCnt & "].TtwcapA1"
            Worksheets("q_rglsdl_ann6").Cells(j, 2).Value = Worksheets("q_rglsdl").Cells(i, 3).Value
            j = j + 1
        
            Worksheets("q_rglsdl_ann6").Cells(j, 1).Value = "FDCAP.SLIPA[" & stockCnt & "].TtwcapA2"
            Worksheets("q_rglsdl_ann6").Cells(j, 2).Value = Worksheets("q_rglsdl").Cells(i, 4).Value
            j = j + 1
        
            'Worksheets("q_rglsdl_ann6").Cells(j, 1).Value = "FDCAP.SLIPA[" & stockCnt & "].TtwcapA3"
            'j = j + 1
        
            'Worksheets("q_rglsdl_ann6").Cells(j, 1).Value = "FDCAP.SLIPA[" & stockCnt & "].TtwcapA4"
            'j = j + 1
        
            Worksheets("q_rglsdl_ann6").Cells(j, 1).Value = "FDCAP.SLIPA[" & stockCnt & "].TtwcapA5"
            Worksheets("q_rglsdl_ann6").Cells(j, 2).Value = Worksheets("q_rglsdl").Cells(i, 6).Value
            j = j + 1
        
            Worksheets("q_rglsdl_ann6").Cells(j, 1).Value = "FDCAP.SLIPA[" & stockCnt & "].TtwcapA6"
            Worksheets("q_rglsdl_ann6").Cells(j, 2).Value = Worksheets("q_rglsdl").Cells(i, 5).Value
            j = j + 1
        
            'Worksheets("q_rglsdl_ann6").Cells(j, 1).Value = "FDCAP.SLIPA[" & stockCnt & "].TtwcapA7"
            'j = j + 1
        
            Worksheets("q_rglsdl_ann6").Cells(j, 1).Value = "FDCAP.SLIPA[" & stockCnt & "].TtwcapA9"
            Worksheets("q_rglsdl_ann6").Cells(j, 2).Value = foreign_text
            j = j + 1
        
        End If
        
    End If
    
    i = i + 1
Loop

Worksheets("q_rglsdl_ann6").Cells(1, 1).Activate

ActiveCell.EntireRow.Insert

Worksheets("q_rglsdl_ann6").Cells(1, 1).Value = "[|0|1]"

End Sub


Sub SearchForFiles()

With Application.FileSearch
    .NewSearch
    .LookIn = "U:\Users"
    .SearchSubFolders = False
    
    .Filename = "Run"
    .MatchTextExactly = True
    .FileType = msoFileTypeAllFiles
    
    If .Execute() > 0 Then
        MsgBox "There were " & .FoundFiles.Count & _
            " file(s) found."
        For i = 1 To .FoundFiles.Count
            MsgBox .FoundFiles(i)
        Next i
    Else
        MsgBox "There were no files found."
    End If
End With
        


End Sub

Sub DeleteQueryTables()

Dim qt As Integer
For qt = ActiveSheet.QueryTables.Count To 1 Step -1
    ActiveSheet.QueryTables.Item(qt).Delete
Next qt

End Sub

Sub q_iedl_ann3_new()

Workbooks("q_acntdl.xls").Worksheets.Add
ActiveSheet.Name = "q_iedl_ann3"

i = 8

j = 1

blankCnt = 0
dividendCnt = 0
country_text = ""
currency_text = ""
category_text = ""

Do While blankCnt < 10
    If Worksheets("q_iedl").Cells(i, 4).Value = "" Then
        blankCnt = blankCnt + 1
    Else
        blankCnt = 0
        If Worksheets("q_iedl").Cells(i - 1, 4).Value = "" And _
            Worksheets("q_iedl").Cells(i - 3, 1).Value <> "" Then
            country_text = Worksheets("q_iedl").Cells(i - 3, 1).Value
        End If
        If Worksheets("q_iedl").Cells(i - 1, 4).Value = "" And _
            Worksheets("q_iedl").Cells(i - 2, 2).Value <> "" Then
            currency_text = Worksheets("q_iedl").Cells(i - 2, 2).Value
        End If
        If Worksheets("q_iedl").Cells(i - 1, 4).Value = "" And _
            Worksheets("q_iedl").Cells(i - 1, 3).Value <> "" Then
            category_text = Worksheets("q_iedl").Cells(i - 1, 3).Value
        End If
    
        ' If its a dividend
        If InStr(category_text, "ividend") > 0 Then
        
            ' From Canada
            'If country_text = "Canada" Then
            If (Worksheets("q_iedl").Cells(i, 14).Value = "ca") Then
                dividendCnt = dividendCnt + 1
                Worksheets("q_iedl_ann3").Cells(j, 1).Value = "FDDIV.SLIPA[" & dividendCnt & "].TtadivA1"
                Worksheets("q_iedl_ann3").Cells(j, 2).Value = Worksheets("q_iedl").Cells(i, 6).Value
                j = j + 1
                
                'Worksheets("q_iedl_ann3").Cells(j, 1).Value = "FDDIV.SLIPA[" & dividendCnt & "].TtadivA2"
                'If country_text <> "Canada" Then
                '    Worksheets("q_iedl_ann3").Cells(j, 2).Value = "X"
                'End If
                'j = j + 1
                
                Worksheets("q_iedl_ann3").Cells(j, 1).Value = "FDDIV.SLIPA[" & dividendCnt & "].TtadivA7"
                Worksheets("q_iedl_ann3").Cells(j, 2).Value = Worksheets("q_iedl").Cells(i, 11).Value
                j = j + 1
                
                Worksheets("q_iedl_ann3").Cells(j, 1).Value = "FDDIV.SLIPA[" & dividendCnt & "].TtadivA11"
                Worksheets("q_iedl_ann3").Cells(j, 2).Value = Worksheets("q_iedl").Cells(i, 11).Value
                j = j + 1
                
                Worksheets("q_iedl_ann3").Cells(j, 1).Value = "FDDIV.SLIPA[" & dividendCnt & "].TtadivA12"
                Worksheets("q_iedl_ann3").Cells(j, 2).Value = 1
                j = j + 1
            End If
        Else
        
            Do
                i = i + 1
            Loop Until Worksheets("q_iedl").Cells(i, 4).Value = ""
        
        End If
    End If
    
    i = i + 1
Loop

Worksheets("q_iedl_ann3").Cells(1, 1).Activate

ActiveCell.EntireRow.Insert

Worksheets("q_iedl_ann3").Cells(1, 1).Value = "[|0|1]"


End Sub




