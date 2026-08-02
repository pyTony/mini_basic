def test_regular_array_substitution_and_access(self):
        """Verify that basic 1D and 2D arrays dimension, assign, and substitute correctly."""
        from mini_basic.runtime import BASICInterpreter
        
        interp = BASICInterpreter()
        # Initialize basic program allocating and referencing arrays
        interp.program = {
            10: "DIM A(5)",
            20: "DIM B%(2,2)",
            30: "A(1) = 42",
            40: "B%(1,2) = 100",
            50: "PRINT A(1)",
            60: "PRINT B%(1,2)"
        }
        
        # Pre-process the definitions as standard execution blocks
        interp._definitions_dirty = True
        interp._prepare_program_for_run()
        
        # Execute DIM allocations manually or via program sequence
        interp._execute_statement(None, "DIM A(5)")
        interp._execute_statement(None, "DIM B%(2,2)")
        
        # 1. Test explicit assignment processing (uses lvalue parsing)
        interp._execute_statement(None, "A(1) = 42")
        interp._execute_statement(None, "B%(1,2) = 100")
        
        # 2. Test expression evaluation and substitutions
        # This confirms _substitute_array_references properly intercepts and replaces them
        val_a = interp.eval_expr("A(1)")
        val_b = interp.eval_expr("B%(1,2)")
        
        self.assertEqual(float(val_a), 42.0)
        self.assertEqual(int(val_b), 100)
