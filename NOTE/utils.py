from fpdf import FPDF

class BulletinPDF(FPDF):
    # Ajout du paramètre 'classe' ici
    def header_bulletin(self, ecole, classe, eleve, periode, annee):
        self.set_font("helvetica", "B", 15)
        self.cell(0, 8, f"ECOLE : {ecole.nom.upper()}", ln=True, align='C')
        self.set_font("helvetica", "I", 10)
        self.cell(0, 5, "République du Mali - Ministère de l'Éducation", ln=True, align='C')
        self.ln(5)
        
        self.set_fill_color(230, 230, 230)
        self.set_font("helvetica", "B", 12)
        p_label = periode.replace('_', ' ')
        self.cell(0, 10, f"BULLETIN DE NOTES : {p_label}", border=1, ln=True, align='C', fill=True)
        self.ln(5)
        
        self.set_font("helvetica", "", 10)
        self.cell(100, 7, f"NOM : {eleve.nom.upper()}", ln=False)
        self.cell(0, 7, f"CLASSE : {classe.nom}", ln=True) # ✅ CORRIGÉ : utilise directement l'objet classe
        self.cell(100, 7, f"PRÉNOMS : {eleve.prenom}", ln=False)
        self.cell(0, 7, f"ANNÉE SCOLAIRE : {annee}", ln=True)
        self.ln(5)

    def draw_table_header(self, is_primaire):
        self.set_fill_color(37, 99, 235) 
        self.set_text_color(255, 255, 255)
        self.set_font("helvetica", "B", 9)
        
        if is_primaire:
            self.cell(80, 8, "MATIÈRES", border=1, fill=True)
            self.cell(50, 8, "NOTE MENSUELLE", border=1, fill=True, align='C')
            self.cell(60, 8, "APPRÉCIATIONS", border=1, fill=True, align='C', ln=True)
        else:
            self.cell(60, 8, "MATIÈRES", border=1, fill=True)
            self.cell(20, 8, "MOY. DEV", border=1, fill=True, align='C')
            self.cell(20, 8, "COMP.", border=1, fill=True, align='C')
            self.cell(20, 8, "MOY/20", border=1, fill=True, align='C')
            self.cell(15, 8, "COEF", border=1, fill=True, align='C')
            self.cell(25, 8, "TOTAL", border=1, fill=True, align='C')
            self.cell(30, 8, "APPRÉCIATION", border=1, fill=True, align='C', ln=True)
        
        self.set_text_color(0, 0, 0)

    def get_appreciation(self, note):
        if note >= 16: return "Excellent"
        elif note >= 14: return "Très Bien"
        elif note >= 12: return "Bien"
        elif note >= 10: return "Passable"
        elif note >= 8: return "Insuffisant"
        elif note > 0: return "Médiocre"
        else: return "-"

    # Ajout du paramètre 'classe' ici également
    def generer_tableau(self, ecole, classe, eleve, matieres, notes_dict, coeffs, periode, moy_gen, rang, effectif, annee_nom):
        periodes_secondaire = ['TRIMESTRE_1', 'TRIMESTRE_2', 'TRIMESTRE_3']
        is_primaire = periode not in periodes_secondaire

        # ✅ Transmet la classe au header du bulletin
        self.header_bulletin(ecole, classe, eleve, periode, annee_nom)
        self.draw_table_header(is_primaire)
    
        self.set_font("helvetica", "", 9)
        total_points = 0
        total_coeffs = 0

        for m in matieres:
            n = notes_dict.get(m.id, {})
            coef = coeffs.get(m.id, 1)
            
            if is_primaire:
                val = n.get('MENSUELLE', 0)
                appreciation = self.get_appreciation(val)
                
                self.cell(80, 8, f" {m.nom}", border=1)
                self.cell(50, 8, f"{val:.2f}", border=1, align='C')
                self.cell(60, 8, appreciation, border=1, align='C', ln=True)
                
                total_points += val
                total_coeffs += 1
            else:
                d1 = n.get('DEVOIR_1', None)
                d2 = n.get('DEVOIR_2', None)
                comp = n.get('COMPOSITION', 0)
                
                nb_dev = 0
                somme_dev = 0
                if d1 is not None: 
                    somme_dev += d1
                    nb_dev += 1
                if d2 is not None: 
                    somme_dev += d2
                    nb_dev += 1
                
                moy_dev = (somme_dev / nb_dev) if nb_dev > 0 else 0
                moy_mat = (moy_dev + (comp * 2)) / 3 if (comp > 0 or moy_dev > 0) else 0
                    
                pts = moy_mat * coef
                appreciation = self.get_appreciation(moy_mat)
            
                self.cell(60, 8, f" {m.nom}", border=1)
                self.cell(20, 8, f"{moy_dev:.2f}", border=1, align='C')
                self.cell(20, 8, f"{comp:.2f}", border=1, align='C')
                self.cell(20, 8, f"{moy_mat:.2f}", border=1, align='C')
                self.cell(15, 8, f"{coef}", border=1, align='C')
                self.cell(25, 8, f"{pts:.2f}", border=1, align='C')
                self.cell(30, 8, appreciation, border=1, align='C', ln=True)
            
                total_points += pts
                total_coeffs += coef

        # --- BLOC DE SYNTHÈSE ---
        self.ln(2)
        self.set_font("helvetica", "B", 10)
        
        self.cell(135 if not is_primaire else 80, 10, "TOTAL DES POINTS", border=1, align='R')
        self.cell(55 if not is_primaire else 50, 10, f"{total_points:.2f}", border=1, align='C', ln=True)

        self.set_fill_color(230, 240, 255)
        self.cell(135 if not is_primaire else 80, 10, "MOYENNE GÉNÉRALE", border=1, align='R', fill=True)
        self.cell(55 if not is_primaire else 50, 10, f"{moy_gen:.2f} / 20", border=1, align='C', ln=True, fill=True)

        suffixe = "er" if rang == 1 else "ème"
        self.cell(135 if not is_primaire else 80, 10, "RANG", border=1, align='R')
        self.cell(55 if not is_primaire else 50, 10, f"{rang}{suffixe} sur {effectif}", border=1, align='C', ln=True)

        self.ln(10)
        self.cell(60, 10, "Le Parent", ln=0, align='C')
        self.cell(130, 10, "Le Directeur", ln=1, align='C')