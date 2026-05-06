"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/Dialog";
import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/hooks/useThemeTokens";

interface RenameChatDialogProps {
  open: boolean;
  initialTitle: string;
  onClose: () => void;
  onConfirm: (newTitle: string) => void;
}

export function RenameChatDialog({
  open,
  initialTitle,
  onClose,
  onConfirm,
}: RenameChatDialogProps) {
  const t = useThemeTokens();
  const [value, setValue] = useState(initialTitle);

  useEffect(() => {
    if (open) setValue(initialTitle);
  }, [open, initialTitle]);

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed) {
      onClose();
      return;
    }
    onConfirm(trimmed);
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className={cn(t.glassPanel, t.textMain, "max-w-sm")}>
        <DialogHeader>
          <DialogTitle>Переименовать беседу</DialogTitle>
        </DialogHeader>
        <input
          autoFocus
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") submit();
          }}
          placeholder="Новое название..."
          className={cn(
            "w-full px-3 py-2 rounded-xl outline-none transition-colors text-base",
            t.inputWrapper,
            t.textMain,
          )}
        />
        <DialogFooter>
          <Button variant="ghost" onClick={onClose} className={t.textMain}>
            Отмена
          </Button>
          <Button onClick={submit}>Сохранить</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
