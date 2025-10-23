import { useState } from "react";
import { X, BookOpen, Workflow, Lightbulb, HelpCircle, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

interface HelpDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type HelpTab = "getting-started" | "pipeline" | "workflows" | "faq" | "about";

export function HelpDialog({ open, onOpenChange }: HelpDialogProps) {
  const [activeTab, setActiveTab] = useState<HelpTab>("getting-started");

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-background/80 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />

      {/* Dialog */}
      <div className="relative z-50 w-full max-w-3xl max-h-[85vh] rounded-lg border border-border bg-card shadow-lg flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">AssetForge Help</h2>
          </div>
          <button
            onClick={() => onOpenChange(false)}
            className={cn(
              "inline-flex h-8 w-8 items-center justify-center rounded-md",
              "hover:bg-accent hover:text-accent-foreground",
              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            )}
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 px-6 pt-4 border-b border-border">
          <button
            onClick={() => setActiveTab("getting-started")}
            className={cn(
              "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-t-md transition-colors",
              "hover:bg-accent hover:text-accent-foreground",
              activeTab === "getting-started" && "bg-primary text-primary-foreground"
            )}
          >
            <Lightbulb className="h-4 w-4" />
            Getting Started
          </button>
          <button
            onClick={() => setActiveTab("pipeline")}
            className={cn(
              "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-t-md transition-colors",
              "hover:bg-accent hover:text-accent-foreground",
              activeTab === "pipeline" && "bg-primary text-primary-foreground"
            )}
          >
            <Workflow className="h-4 w-4" />
            Pipeline
          </button>
          <button
            onClick={() => setActiveTab("workflows")}
            className={cn(
              "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-t-md transition-colors",
              "hover:bg-accent hover:text-accent-foreground",
              activeTab === "workflows" && "bg-primary text-primary-foreground"
            )}
          >
            <BookOpen className="h-4 w-4" />
            Workflows
          </button>
          <button
            onClick={() => setActiveTab("faq")}
            className={cn(
              "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-t-md transition-colors",
              "hover:bg-accent hover:text-accent-foreground",
              activeTab === "faq" && "bg-primary text-primary-foreground"
            )}
          >
            <HelpCircle className="h-4 w-4" />
            FAQ & Tips
          </button>
          <button
            onClick={() => setActiveTab("about")}
            className={cn(
              "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-t-md transition-colors",
              "hover:bg-accent hover:text-accent-foreground",
              activeTab === "about" && "bg-primary text-primary-foreground"
            )}
          >
            <FileText className="h-4 w-4" />
            About & License
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === "getting-started" && <GettingStartedContent />}
          {activeTab === "pipeline" && <PipelineContent />}
          {activeTab === "workflows" && <WorkflowsContent />}
          {activeTab === "faq" && <FAQContent />}
          {activeTab === "about" && <AboutContent />}
        </div>
      </div>
    </div>
  );
}

function GettingStartedContent() {
  return (
    <div className="space-y-6 prose prose-sm dark:prose-invert max-w-none">
      <div>
        <h3 className="text-lg font-semibold mb-3">Welcome to AssetForge</h3>
        <p className="text-muted-foreground">
          AssetForge is an autonomous AI pipeline that researches, designs, and generates complete digital product bundles ready for marketplaces like Etsy and Gumroad.
        </p>
      </div>

      <div>
        <h4 className="font-semibold mb-2">1. Get Your OpenAI API Key</h4>
        <p className="text-sm text-muted-foreground mb-2">
          AssetForge uses OpenAI's models to power its AI pipeline. You'll need an API key:
        </p>
        <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground ml-4">
          <li>Visit <code className="px-1 py-0.5 bg-muted rounded text-xs">platform.openai.com/api-keys</code></li>
          <li>Sign in or create an account</li>
          <li>Click "Create new secret key"</li>
          <li>Copy the key (starts with <code className="px-1 py-0.5 bg-muted rounded text-xs">sk-...</code>)</li>
          <li>Paste it into AssetForge Settings (⚙️ icon in header)</li>
        </ol>
        <p className="text-xs text-muted-foreground mt-2 bg-blue-50 dark:bg-blue-950/30 p-3 rounded border border-blue-200 dark:border-blue-900">
          <strong>Note:</strong> Your API key is stored securely in your system keyring and never transmitted except to OpenAI's servers.
        </p>
      </div>

      <div>
        <h4 className="font-semibold mb-2">2. Choose Your Workflow</h4>
        <p className="text-sm text-muted-foreground mb-2">
          AssetForge offers different modes depending on how much control you want:
        </p>
        <ul className="list-disc list-inside space-y-2 text-sm text-muted-foreground ml-4">
          <li><strong>Research Ideas:</strong> Generate product ideas without building anything yet</li>
          <li><strong>Quick Build (Auto-Pick):</strong> Auto-selects the best idea from your library and builds it fully</li>
          <li><strong>Browse & Select Idea:</strong> Manually pick an idea from your library to build</li>
          <li><strong>Research & Auto-Build:</strong> Full autonomous pipeline - researches, plans, builds, and packages automatically</li>
        </ul>
      </div>

      <div>
        <h4 className="font-semibold mb-2">3. Understanding the Library</h4>
        <p className="text-sm text-muted-foreground mb-2">
          The Library tab is your workspace where you manage:
        </p>
        <ul className="list-disc list-inside space-y-2 text-sm text-muted-foreground ml-4">
          <li><strong>Ideas:</strong> Product concepts from research - turn these into bundle plans</li>
          <li><strong>Ready to Make:</strong> Planned bundles waiting for asset generation</li>
          <li><strong>Ready to Package:</strong> Generated assets waiting to be packaged</li>
        </ul>
      </div>

      <div className="bg-amber-50 dark:bg-amber-950/30 p-4 rounded border border-amber-200 dark:border-amber-900">
        <h4 className="font-semibold mb-2 text-amber-900 dark:text-amber-100">First Time? Try This:</h4>
        <ol className="list-decimal list-inside space-y-1 text-sm text-amber-900/80 dark:text-amber-100/80 ml-4">
          <li>Click Settings (⚙️) and add your OpenAI API key</li>
          <li>Go to Generate tab and click "Research Ideas"</li>
          <li>Watch the AI discover profitable digital product niches</li>
          <li>When complete, click "Generate Bundle" → "Quick Build (Auto-Pick)"</li>
          <li>Or browse ideas in Library tab and manually select one to build</li>
        </ol>
      </div>
    </div>
  );
}

function PipelineContent() {
  return (
    <div className="space-y-6 prose prose-sm dark:prose-invert max-w-none">
      <div>
        <h3 className="text-lg font-semibold mb-3">Understanding the 4-Step Pipeline</h3>
        <p className="text-muted-foreground">
          AssetForge uses a structured AI pipeline to create complete digital product bundles:
        </p>
      </div>

      <div className="space-y-4">
        <div className="border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-950/30 p-4 rounded">
          <div className="flex items-center gap-2 mb-2">
            <div className="h-8 w-8 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm font-bold">1</div>
            <h4 className="font-semibold">Researcher</h4>
          </div>
          <p className="text-sm text-muted-foreground mb-2">
            Analyzes marketplaces to find profitable digital product niches.
          </p>
          <ul className="list-disc list-inside text-sm text-muted-foreground ml-4 space-y-1">
            <li>Researches trending categories and keywords</li>
            <li>Evaluates competition and demand</li>
            <li>Generates ranked product ideas</li>
            <li>Saves ideas to your Library for review</li>
          </ul>
        </div>

        <div className="border-l-4 border-purple-500 bg-purple-50 dark:bg-purple-950/30 p-4 rounded">
          <div className="flex items-center gap-2 mb-2">
            <div className="h-8 w-8 rounded-full bg-purple-500 text-white flex items-center justify-center text-sm font-bold">2</div>
            <h4 className="font-semibold">Planner</h4>
          </div>
          <p className="text-sm text-muted-foreground mb-2">
            Designs the complete bundle structure and metadata.
          </p>
          <ul className="list-disc list-inside text-sm text-muted-foreground ml-4 space-y-1">
            <li>Creates bundle plan (assets, pricing, personas)</li>
            <li>Defines store titles and descriptions</li>
            <li>Plans asset structure and content</li>
            <li>Saves plan to Library "Ready to Make" section</li>
          </ul>
        </div>

        <div className="border-l-4 border-green-500 bg-green-50 dark:bg-green-950/30 p-4 rounded">
          <div className="flex items-center gap-2 mb-2">
            <div className="h-8 w-8 rounded-full bg-green-500 text-white flex items-center justify-center text-sm font-bold">3</div>
            <h4 className="font-semibold">Maker</h4>
          </div>
          <p className="text-sm text-muted-foreground mb-2">
            Generates the actual digital assets and store metadata.
          </p>
          <ul className="list-disc list-inside text-sm text-muted-foreground ml-4 space-y-1">
            <li>Creates digital files (PDFs, templates, guides)</li>
            <li>Generates Etsy and Gumroad metadata</li>
            <li>Runs quality assurance checks</li>
            <li>Saves assets to Library "Ready to Package" section</li>
          </ul>
        </div>

        <div className="border-l-4 border-orange-500 bg-orange-50 dark:bg-orange-950/30 p-4 rounded">
          <div className="flex items-center gap-2 mb-2">
            <div className="h-8 w-8 rounded-full bg-orange-500 text-white flex items-center justify-center text-sm font-bold">4</div>
            <h4 className="font-semibold">Packager</h4>
          </div>
          <p className="text-sm text-muted-foreground mb-2">
            Finalizes the bundle and prepares it for marketplace upload.
          </p>
          <ul className="list-disc list-inside text-sm text-muted-foreground ml-4 space-y-1">
            <li>Organizes metadata and assets</li>
            <li>Converts files to final formats</li>
            <li>Validates bundle structure</li>
            <li>Saves completed bundle to output folder</li>
          </ul>
        </div>
      </div>

      <div className="bg-slate-100 dark:bg-slate-800 p-4 rounded">
        <p className="text-sm text-muted-foreground">
          <strong>Progress Tracking:</strong> Watch the pipeline status chips at the top of the Generate tab to see which step is currently running. Each step shows real-time progress and logs.
        </p>
      </div>
    </div>
  );
}

function WorkflowsContent() {
  return (
    <div className="space-y-6 prose prose-sm dark:prose-invert max-w-none">
      <div>
        <h3 className="text-lg font-semibold mb-3">Common Workflows</h3>
        <p className="text-muted-foreground">
          Choose the workflow that best fits your needs:
        </p>
      </div>

      <div className="space-y-4">
        <div className="border border-border rounded-lg p-4">
          <h4 className="font-semibold mb-2">Workflow 1: Research Ideas</h4>
          <p className="text-sm text-muted-foreground mb-3">
            Best for exploring ideas before committing to building anything.
          </p>
          <ol className="list-decimal list-inside space-y-1.5 text-sm text-muted-foreground ml-4">
            <li>Go to <strong>Generate</strong> tab</li>
            <li>Click <strong>Research Ideas</strong> button</li>
            <li>Wait for AI to discover product niches</li>
            <li>Navigate to <strong>Library → Ideas</strong></li>
            <li>Review ideas and choose what to build next</li>
          </ol>
          <div className="mt-3 text-xs bg-blue-50 dark:bg-blue-950/30 p-2 rounded">
            <strong>Use when:</strong> You want to explore multiple ideas before building
          </div>
        </div>

        <div className="border border-border rounded-lg p-4">
          <h4 className="font-semibold mb-2">Workflow 2: Quick Build (Auto-Pick)</h4>
          <p className="text-sm text-muted-foreground mb-3">
            Auto-selects the best idea and builds it fully - no research needed.
          </p>
          <ol className="list-decimal list-inside space-y-1.5 text-sm text-muted-foreground ml-4">
            <li>First, run <strong>Research Ideas</strong> to build your idea library</li>
            <li>Go to <strong>Generate</strong> tab</li>
            <li>Click <strong>Generate Bundle</strong> → <strong>Quick Build (Auto-Pick)</strong></li>
            <li>AI selects the best idea and runs Planner → Maker → Packager</li>
            <li>Get your completed bundle</li>
          </ol>
          <div className="mt-3 text-xs bg-purple-50 dark:bg-purple-950/30 p-2 rounded">
            <strong>Use when:</strong> You have ideas ready and want the AI to pick the best one
          </div>
        </div>

        <div className="border border-border rounded-lg p-4">
          <h4 className="font-semibold mb-2">Workflow 3: Browse & Select Idea</h4>
          <p className="text-sm text-muted-foreground mb-3">
            Maximum control - manually pick which idea to build.
          </p>
          <ol className="list-decimal list-inside space-y-1.5 text-sm text-muted-foreground ml-4">
            <li>First, run <strong>Research Ideas</strong> to build your idea library</li>
            <li>Click <strong>Generate Bundle</strong> → <strong>Browse & Select Idea</strong></li>
            <li>Or navigate to <strong>Library → Ideas</strong></li>
            <li>Review ideas and click <strong>Build Plan</strong> or <strong>Build Full Bundle</strong></li>
            <li>Continue step-by-step or let it complete fully</li>
          </ol>
          <div className="mt-3 text-xs bg-amber-50 dark:bg-amber-950/30 p-2 rounded">
            <strong>Use when:</strong> You want to manually review and select which idea to build
          </div>
        </div>

        <div className="border border-border rounded-lg p-4">
          <h4 className="font-semibold mb-2">Workflow 4: Research & Auto-Build (Thorough)</h4>
          <p className="text-sm text-muted-foreground mb-3">
            Fully autonomous - researches new ideas and builds automatically.
          </p>
          <ol className="list-decimal list-inside space-y-1.5 text-sm text-muted-foreground ml-4">
            <li>Go to <strong>Generate</strong> tab</li>
            <li>Click <strong>Generate Bundle</strong> → <strong>Research & Auto-Build</strong></li>
            <li>AI runs complete pipeline: Research → Plan → Make → Package</li>
            <li>Wait for all 4 steps to complete</li>
            <li>Get your completed bundle</li>
          </ol>
          <div className="mt-3 text-xs bg-green-50 dark:bg-green-950/30 p-2 rounded">
            <strong>Use when:</strong> You want a fresh research pass and full automation
          </div>
        </div>
      </div>

      <div className="bg-slate-100 dark:bg-slate-800 p-4 rounded">
        <p className="text-sm font-semibold mb-2">Viewing History</p>
        <p className="text-sm text-muted-foreground">
          All completed bundles are saved in the <strong>History</strong> tab, where you can review details and open output folders.
        </p>
      </div>
    </div>
  );
}

function AboutContent() {
  return (
    <div className="space-y-6 prose prose-sm dark:prose-invert max-w-none">
      <div>
        <h3 className="text-lg font-semibold mb-3">About AssetForge</h3>
        <div className="space-y-2 text-sm text-muted-foreground">
          <p><strong>Version:</strong> 1.0.7</p>
          <p><strong>Copyright:</strong> © 2025 AssetForge. All Rights Reserved.</p>
          <p><strong>Description:</strong> One-Click Digital Asset Factory - An autonomous, schema-driven pipeline that generates complete digital product bundles for marketplaces.</p>
        </div>
      </div>

      <div>
        <h4 className="font-semibold mb-3">Software License Agreement</h4>
        <div className="bg-muted rounded-lg p-4 text-xs font-mono overflow-y-auto max-h-96 whitespace-pre-wrap border border-border">
{`PROPRIETARY SOFTWARE LICENSE AGREEMENT

Copyright (c) 2025 AssetForge. All Rights Reserved.

This software and associated documentation files (the "Software") are proprietary
and confidential to AssetForge.

GRANT OF LICENSE

Subject to the terms of this Agreement and payment of the applicable license fee,
you are granted a limited, non-exclusive, non-transferable license to:

1. Install and use the Software on devices you own or control
2. Use the Software for personal or commercial purposes

RESTRICTIONS

You may NOT:

1. Distribute, sell, lease, rent, lend, or sublicense the Software
2. Modify, reverse engineer, decompile, or disassemble the Software
3. Remove or alter any proprietary notices or labels on the Software
4. Share your copy of the Software with others
5. Use the Software to provide services to third parties
6. Create derivative works based on the Software

INTELLECTUAL PROPERTY

All title, ownership rights, and intellectual property rights in and to the
Software remain with AssetForge. The Software is protected by copyright laws
and international treaty provisions.

TERMINATION

This license is effective until terminated. Your rights under this license will
terminate automatically without notice if you fail to comply with any term of
this Agreement.

NO WARRANTY

THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE, AND NONINFRINGEMENT. THE ENTIRE RISK AS TO THE QUALITY AND
PERFORMANCE OF THE SOFTWARE IS WITH YOU.

LIMITATION OF LIABILITY

IN NO EVENT SHALL ASSETFORGE BE LIABLE FOR ANY SPECIAL, INCIDENTAL, INDIRECT, OR
CONSEQUENTIAL DAMAGES WHATSOEVER (INCLUDING, WITHOUT LIMITATION, DAMAGES FOR LOSS
OF BUSINESS PROFITS, BUSINESS INTERRUPTION, LOSS OF BUSINESS INFORMATION, OR ANY
OTHER PECUNIARY LOSS) ARISING OUT OF THE USE OF OR INABILITY TO USE THE SOFTWARE.

GOVERNING LAW

This Agreement shall be governed by and construed in accordance with the laws of
the jurisdiction in which AssetForge operates, without regard to its conflict of
law provisions.

By installing or using the Software, you acknowledge that you have read this
Agreement, understand it, and agree to be bound by its terms and conditions.`}
        </div>
        <p className="text-xs text-muted-foreground mt-3">
          By using AssetForge, you acknowledge that you have read and agree to this license agreement.
        </p>
      </div>
    </div>
  );
}

function FAQContent() {
  return (
    <div className="space-y-4 prose prose-sm dark:prose-invert max-w-none">
      <h3 className="text-lg font-semibold mb-3">Frequently Asked Questions</h3>

      <div className="space-y-4">
        <div>
          <h4 className="font-semibold text-sm mb-1">How much does it cost to run?</h4>
          <p className="text-sm text-muted-foreground">
            AssetForge itself is a one-time purchase, but it uses your OpenAI API key.
            Each full bundle typically costs ~$2-5 in API usage. You only pay for what you generate.
          </p>
        </div>

        <div>
          <h4 className="font-semibold text-sm mb-1">How many ideas does research generate?</h4>
          <p className="text-sm text-muted-foreground">
            Each research run generates exactly 6 product ideas. This limit ensures reliable completion and prevents
            OpenAI API timeouts that can occur during extensive web searching with larger batches.
          </p>
        </div>

        <div>
          <h4 className="font-semibold text-sm mb-1">Where are my files stored?</h4>
          <p className="text-sm text-muted-foreground">
            All outputs are saved locally in <code className="px-1 py-0.5 bg-muted rounded text-xs">%APPDATA%/assetforge/data/</code> on Windows.
            You can click "Open in Explorer" from result panels to access them directly.
          </p>
        </div>

        <div>
          <h4 className="font-semibold text-sm mb-1">Is my API key secure?</h4>
          <p className="text-sm text-muted-foreground">
            Yes! Your API key is stored in your system keyring (Windows Credential Manager) and never transmitted
            anywhere except directly to OpenAI's API. It's never sent to AssetForge servers (there are none!).
          </p>
        </div>

        <div>
          <h4 className="font-semibold text-sm mb-1">Can I edit the generated assets?</h4>
          <p className="text-sm text-muted-foreground">
            Absolutely! All generated files are standard formats (PDFs, JSON, etc.) that you can edit with any tool.
            Open the output folder and customize as needed before uploading to marketplaces.
          </p>
        </div>

        <div>
          <h4 className="font-semibold text-sm mb-1">What if the pipeline fails mid-way?</h4>
          <p className="text-sm text-muted-foreground">
            Don't worry! AssetForge saves progress at each step. If the Maker step fails, your bundle plan is still
            saved in Library → Ready to Make. Just click "Generate Assets" again to retry.
          </p>
        </div>

        <div>
          <h4 className="font-semibold text-sm mb-1">Can I run multiple bundles at once?</h4>
          <p className="text-sm text-muted-foreground">
            Not currently - AssetForge processes one bundle at a time to ensure quality. Queue up multiple ideas
            in your Library and process them sequentially.
          </p>
        </div>

        <div>
          <h4 className="font-semibold text-sm mb-1">How do I delete old ideas or bundles?</h4>
          <p className="text-sm text-muted-foreground">
            In the Library tab, hover over any item and click the trash icon. You can also bulk delete from
            the dropdown menu in each library section.
          </p>
        </div>
      </div>

      <div className="bg-green-50 dark:bg-green-950/30 p-4 rounded border border-green-200 dark:border-green-900 mt-6">
        <h4 className="font-semibold text-sm mb-2">Pro Tips</h4>
        <ul className="list-disc list-inside space-y-1.5 text-sm text-muted-foreground ml-4">
          <li>Start with Research Ideas to build up an idea library before committing</li>
          <li>Use Quick Build (Auto-Pick) when you have ideas ready and want fast results</li>
          <li>Use Browse & Select for maximum control over which ideas to build</li>
          <li>Review bundle plans before generating assets - it's much faster to iterate on plans</li>
          <li>Keep your successful bundles in History for reference when creating similar products</li>
        </ul>
      </div>
    </div>
  );
}
